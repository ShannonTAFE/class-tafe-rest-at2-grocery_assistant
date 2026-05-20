import asyncio
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from fastmcp import Client
from google import genai
from google.genai import types


load_dotenv()

MCP_URL = os.getenv("GROCERY_MCP_URL", "http://127.0.0.1:8000/mcp")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


GROCERY_SYSTEM_INSTRUCTION = """
You are a grocery planning assistant connected to the user's Grocery Assistant MCP server.

You can use MCP-backed tools to inspect inventory, intake, planning context,
low-stock items, use-soon items, data quality signals, restock suggestions,
and meal suggestions.

Important behaviour:
- Prefer read, review, and draft tools before write tools.
- Do not modify inventory or intake unless the user clearly asks for a stored data change.
- If the user asks for advice, suggestions, review, or planning, use read/review/draft tools only.
- Treat recommendation outputs as decision support, not final truth.
- Explain which tool result influenced your answer.
- Respect low-confidence signals, missing data, expiry warnings, and data quality warnings.
- Removal tools are destructive. Only use remove tools when the user clearly asks to delete/remove a record.
"""


# Start read-first. Add write tools later after safety testing.
ALLOWED_MCP_TOOLS = {
    "search_inventory",
    "get_recent_intake",
    "get_daily_intake_summary",
    "search_intake",
    "review_planning_context",
    "review_low_stock_items",
    "review_use_soon_items",
    "review_inventory_data_quality",
    "draft_restock_suggestions_tool",
    "draft_meal_suggestions_tool",
}


def _schema_for_tool(tool_name: str) -> dict[str, Any]:
    """
    Manual Gemini function schemas for your current Grocery MCP tools.

    Keeping these explicit is safer than exposing every MCP tool automatically,
    especially because your server includes write and remove tools.
    """

    common_empty_string = {
        "type": "string",
        "description": "Optional filter. Leave blank if not needed.",
    }

    schemas: dict[str, dict[str, Any]] = {
        "search_inventory": {
            "description": "Search current grocery inventory by query, category, or location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text search across item name, brand, and notes. Use blank for all inventory.",
                    },
                    "category": common_empty_string,
                    "location": common_empty_string,
                },
                "required": ["query", "category", "location"],
            },
        },
        "get_recent_intake": {
            "description": "Get recent food intake entries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of recent intake entries to return.",
                    }
                },
                "required": ["limit"],
            },
        },
        "get_daily_intake_summary": {
            "description": "Get a daily intake summary for a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    }
                },
                "required": ["date"],
            },
        },
        "search_intake": {
            "description": "Search intake history by query and optional date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text search over intake entries/items. Leave blank if not needed.",
                    },
                    "date": {
                        "type": "string",
                        "description": "Optional date in YYYY-MM-DD format. Leave blank if not needed.",
                    },
                },
                "required": ["query", "date"],
            },
        },
        "review_planning_context": {
            "description": "Review current planning context and signals for recommendations.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        "review_low_stock_items": {
            "description": "Review inventory items that are low, very low, or out of stock.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        "review_use_soon_items": {
            "description": "Review inventory items that should be used soon, are expired, or have expiry data issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_use_soon": {
                        "type": "boolean",
                        "description": "Include items nearing expiry.",
                    },
                    "include_expired": {
                        "type": "boolean",
                        "description": "Include expired items.",
                    },
                    "include_no_expiry_data": {
                        "type": "boolean",
                        "description": "Include items missing expiry data.",
                    },
                    "include_invalid_expiry_date": {
                        "type": "boolean",
                        "description": "Include items with invalid expiry dates.",
                    },
                },
                "required": [
                    "include_use_soon",
                    "include_expired",
                    "include_no_expiry_data",
                    "include_invalid_expiry_date",
                ],
            },
        },
        "review_inventory_data_quality": {
            "description": "Review inventory data quality issues and warnings.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        "draft_restock_suggestions_tool": {
            "description": "Draft restock suggestions based on current inventory signals.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        "draft_meal_suggestions_tool": {
            "description": "Draft meal suggestions based on current inventory and planning signals.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }

    return schemas[tool_name]


def build_gemini_tools() -> list[types.Tool]:
    function_declarations = []

    for tool_name in sorted(ALLOWED_MCP_TOOLS):
        schema = _schema_for_tool(tool_name)

        function_declarations.append(
            types.FunctionDeclaration(
                name=tool_name,
                description=schema["description"],
                parameters=schema["parameters"],
            )
        )

    return [types.Tool(function_declarations=function_declarations)]


def extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    parts = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                parts.append(part_text)

    return "\n".join(parts).strip()


def extract_function_calls(response: Any) -> list[Any]:
    calls = []

    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            function_call = getattr(part, "function_call", None)
            if function_call:
                calls.append(function_call)

    return calls


def make_default_args(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    """
    Fill defaults so Gemini can call your MCP tools consistently.
    """

    defaults: dict[str, dict[str, Any]] = {
        "search_inventory": {
            "query": "",
            "category": "",
            "location": "",
        },
        "get_recent_intake": {
            "limit": 10,
        },
        "get_daily_intake_summary": {
            "date": "",
        },
        "search_intake": {
            "query": "",
            "date": "",
        },
        "review_use_soon_items": {
            "include_use_soon": True,
            "include_expired": True,
            "include_no_expiry_data": True,
            "include_invalid_expiry_date": True,
        },
    }

    merged = defaults.get(tool_name, {}).copy()
    merged.update(args or {})
    return merged


async def call_mcp_tool(mcp_client: Client, tool_name: str, args: dict[str, Any]) -> Any:
    if tool_name not in ALLOWED_MCP_TOOLS:
        raise ValueError(f"Tool is not allowed for Gemini client: {tool_name}")

    safe_args = make_default_args(tool_name, args)
    return await mcp_client.call_tool(tool_name, safe_args)


def compact_tool_result(result: Any, max_chars: int = 8000) -> str:
    """
    Convert MCP tool result into compact text for Gemini.

    Prefer structured_content because your smoke test showed structured data
    is available from search_inventory.
    """

    structured = getattr(result, "structured_content", None)
    if structured is not None:
        text = json.dumps(structured, indent=2, ensure_ascii=False)
    else:
        text = str(result)

    if len(text) > max_chars:
        return text[:max_chars] + "\n... [tool result truncated]"

    return text


async def run_gemini_grocery_client(user_request: str) -> None:
    gemini_client = genai.Client()
    gemini_tools = build_gemini_tools()

    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part(text=user_request)],
        )
    ]

    config = types.GenerateContentConfig(
        system_instruction=GROCERY_SYSTEM_INSTRUCTION,
        tools=gemini_tools,
        temperature=0.3,
    )

    async with Client(MCP_URL) as mcp_client:
        await mcp_client.ping()

        first_response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )

        function_calls = extract_function_calls(first_response)

        if not function_calls:
            print(extract_text(first_response))
            return

        for function_call in function_calls:
            tool_name = function_call.name
            tool_args = dict(function_call.args or {})

            print(f"\n[Gemini selected tool: {tool_name}]")
            print(f"[Arguments: {tool_args}]")

            tool_result = await call_mcp_tool(mcp_client, tool_name, tool_args)
            compact_result = compact_tool_result(tool_result)

            contents.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            function_call=types.FunctionCall(
                                name=tool_name,
                                args=tool_args,
                            )
                        )
                    ],
                )
            )

            contents.append(
                types.Content(
                    role="tool",
                    parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={
                                    "result": compact_result,
                                },
                            )
                        )
                    ],
                )
            )

        final_response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=GROCERY_SYSTEM_INSTRUCTION,
                temperature=0.3,
            ),
        )

        print("\nFinal response:\n")
        print(extract_text(final_response))


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]).strip()

    if not request:
        request = "Review my current grocery inventory and suggest what meals I should make soon."

    asyncio.run(run_gemini_grocery_client(request))