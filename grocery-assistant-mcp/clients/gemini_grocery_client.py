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
WRITE TOOL VISIBILITY:
- You are allowed to use write tools when the user's request clearly asks to add, update, consume, or remove stored data.
- Tool calls must be interpretable. The client will print selected tool names and arguments before execution.
- Do not call write tools for advice-only requests.
- For advice, review, meal suggestions, restock suggestions, or planning, prefer review/draft tools.
- If using a write tool, explain afterward what was changed and which tool was used.
- Use remove tools only when the user clearly asks to delete or remove a stored record.
- If a request is ambiguous, do not write. Explain what could be changed instead.
"""


# Start read-first. Add write tools later after safety testing.
ALLOWED_MCP_TOOLS = {
    # Inventory
    "search_inventory",
    "add_inventory_item",
    "update_inventory_item",
    "remove_inventory_item",
    "consume_inventory_item",

    # Intake
    "get_recent_intake",
    "get_daily_intake_summary",
    "search_intake",
    "add_intake_entry",
    "add_intake_item",
    "update_intake_entry",
    "update_intake_item",
    "remove_intake_entry",
    "remove_intake_item",

    # Planning / recommendations
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
                "add_inventory_item": {
            "description": "Add a new item to grocery inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "food_item": {"type": "string"},
                    "brand": {"type": "string"},
                    "category": {"type": "string"},
                    "location": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "servings_remaining": {"type": "number"},
                    "initial_quantity": {"type": "number"},
                    "initial_servings": {"type": "number"},
                    "stock_status": {"type": "string"},
                    "expiry_date": {"type": "string"},
                    "date_added": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": [
                    "food_item",
                    "brand",
                    "category",
                    "location",
                    "quantity",
                    "unit",
                    "servings_remaining",
                    "initial_quantity",
                    "initial_servings",
                    "stock_status",
                    "expiry_date",
                    "date_added",
                    "notes",
                ],
            },
        },
        "update_inventory_item": {
            "description": "Update an existing grocery inventory item by stock_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_id": {"type": "string"},
                    "food_item": {"type": "string"},
                    "brand": {"type": "string"},
                    "category": {"type": "string"},
                    "location": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "servings_remaining": {"type": "number"},
                    "initial_quantity": {"type": "number"},
                    "initial_servings": {"type": "number"},
                    "stock_status": {"type": "string"},
                    "expiry_date": {"type": "string"},
                    "date_added": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["stock_id"],
            },
        },
        "remove_inventory_item": {
            "description": "Remove an inventory item by stock_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_id": {"type": "string"},
                },
                "required": ["stock_id"],
            },
        },
        "consume_inventory_item": {
            "description": "Consume part or all of an inventory item and update remaining quantity/servings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stock_id": {"type": "string"},
                    "quantity_used": {"type": "number"},
                    "servings_used": {"type": "number"},
                    "notes": {"type": "string"},
                },
                "required": ["stock_id", "quantity_used", "servings_used", "notes"],
            },
        },
                "add_intake_entry": {
            "description": "Add a new meal/intake entry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "meal_type": {"type": "string"},
                    "meal_name": {"type": "string"},
                    "meal_description": {"type": "string"},
                    "source": {"type": "string"},
                    "amount_eaten": {"type": "string"},
                    "portion_confidence": {"type": "string"},
                    "total_calories_estimate": {"type": "number"},
                    "total_protein_g_estimate": {"type": "number"},
                    "total_carbs_g_estimate": {"type": "number"},
                    "total_fat_g_estimate": {"type": "number"},
                    "total_fibre_g_estimate": {"type": "number"},
                    "notes": {"type": "string"},
                },
                "required": [
                    "date",
                    "time",
                    "meal_type",
                    "meal_name",
                    "meal_description",
                    "source",
                    "amount_eaten",
                    "portion_confidence",
                    "total_calories_estimate",
                    "total_protein_g_estimate",
                    "total_carbs_g_estimate",
                    "total_fat_g_estimate",
                    "total_fibre_g_estimate",
                    "notes",
                ],
            },
        },
        "add_intake_item": {
            "description": "Add a food item to an existing intake entry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intake_id": {"type": "string"},
                    "food_item": {"type": "string"},
                    "brand": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "calories_estimate": {"type": "number"},
                    "protein_g_estimate": {"type": "number"},
                    "carbs_g_estimate": {"type": "number"},
                    "fat_g_estimate": {"type": "number"},
                    "fibre_g_estimate": {"type": "number"},
                    "source": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": [
                    "intake_id",
                    "food_item",
                    "brand",
                    "quantity",
                    "unit",
                    "calories_estimate",
                    "protein_g_estimate",
                    "carbs_g_estimate",
                    "fat_g_estimate",
                    "fibre_g_estimate",
                    "source",
                    "notes",
                ],
            },
        },
        "update_intake_entry": {
            "description": "Update an existing intake entry by intake_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intake_id": {"type": "string"},
                    "date": {"type": "string"},
                    "time": {"type": "string"},
                    "meal_type": {"type": "string"},
                    "meal_name": {"type": "string"},
                    "meal_description": {"type": "string"},
                    "source": {"type": "string"},
                    "amount_eaten": {"type": "string"},
                    "portion_confidence": {"type": "string"},
                    "total_calories_estimate": {"type": "number"},
                    "total_protein_g_estimate": {"type": "number"},
                    "total_carbs_g_estimate": {"type": "number"},
                    "total_fat_g_estimate": {"type": "number"},
                    "total_fibre_g_estimate": {"type": "number"},
                    "notes": {"type": "string"},
                },
                "required": ["intake_id"],
            },
        },
        "update_intake_item": {
            "description": "Update an existing intake item by intake_item_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intake_item_id": {"type": "string"},
                    "intake_id": {"type": "string"},
                    "food_item": {"type": "string"},
                    "brand": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                    "calories_estimate": {"type": "number"},
                    "protein_g_estimate": {"type": "number"},
                    "carbs_g_estimate": {"type": "number"},
                    "fat_g_estimate": {"type": "number"},
                    "fibre_g_estimate": {"type": "number"},
                    "source": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["intake_item_id"],
            },
        },
        "remove_intake_entry": {
            "description": "Remove an intake entry by intake_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intake_id": {"type": "string"},
                },
                "required": ["intake_id"],
            },
        },
        "remove_intake_item": {
            "description": "Remove an intake item by intake_item_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intake_item_id": {"type": "string"},
                },
                "required": ["intake_item_id"],
            },
        },
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

        tools = await mcp_client.list_tools()
        resources = await mcp_client.list_resources()

        print("\nConnected to Grocery MCP server.")
        print("\nVisible MCP tools:")
        for tool in tools:
            print(f"- {tool.name}")

        print("\nVisible MCP resources:")
        for resource in resources:
            print(f"- {resource.uri}")

        try:
            prompts = await mcp_client.list_prompts()
            print("\nVisible MCP prompts:")
            for prompt in prompts:
                print(f"- {prompt.name}")
        except Exception as exc:
            print(f"\nNo MCP prompts listed or prompt listing unavailable: {exc}")
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

            print("\n" + "=" * 72)
            print("GEMINI TOOL CALL")
            print("=" * 72)
            print(f"Tool: {tool_name}")
            print("Arguments:")
            print(json.dumps(tool_args, indent=2, ensure_ascii=False))
            print("=" * 72)

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