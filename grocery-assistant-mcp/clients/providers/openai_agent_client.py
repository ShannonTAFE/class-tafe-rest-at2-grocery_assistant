"""OpenAI agent client for the Grocery Assistant MCP server.

This is the primary agent path. It lets the OpenAI Agents SDK discover and call
MCP tools exposed by the running Grocery Assistant MCP server.
"""

from __future__ import annotations

import argparse
import asyncio
import os

from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings


DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp"
DEFAULT_OPENAI_AGENT_MODEL = "gpt-5.4-mini"
DEFAULT_REQUEST = "Review my current grocery planning context and suggest useful next actions."

GROCERY_AGENT_INSTRUCTIONS = """
You are a grocery assistant connected to the user's Grocery Assistant MCP server.

PROJECT SCOPE:
- Use the MCP server as the source of truth for inventory, intake, planning, and recommendation signals.
- Prefer review, search, and draft tools for advice, planning, meal ideas, and restock suggestions.
- Do not invent stored records. If a tool result is incomplete, explain the limitation.

WRITE SAFETY:
- Never call add, update, remove, or consume tools unless the user explicitly asks to change stored data.
- If the user asks for advice, review, suggestions, planning, or recommendations, use read/review/draft tools only.
- If a request is ambiguous, explain what could be changed instead of changing data.
- Removal tools are destructive. Only use remove tools when the user clearly asks to delete/remove a record.
- If a write tool is used, explain afterward what changed and which tool was used.
""".strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the OpenAI Grocery Assistant MCP agent client."
    )
    parser.add_argument(
        "request",
        nargs="*",
        help="Natural-language request to send to the grocery agent.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_AGENT_MODEL", DEFAULT_OPENAI_AGENT_MODEL),
        help="OpenAI model to use. Defaults to OPENAI_AGENT_MODEL or project fallback.",
    )
    parser.add_argument(
        "--mcp-url",
        default=os.getenv("GROCERY_MCP_URL", DEFAULT_MCP_URL),
        help="Grocery MCP Streamable HTTP URL.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="MCP server timeout in seconds.",
    )
    return parser


async def run_agent(user_request: str, *, model: str, mcp_url: str, timeout: float) -> str:
    async with MCPServerStreamableHttp(
        name="Grocery Assistant MCP",
        params={
            "url": mcp_url,
            "timeout": timeout,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    ) as grocery_server:
        agent = Agent(
            name="Grocery Assistant Agent",
            instructions=GROCERY_AGENT_INSTRUCTIONS,
            model=model,
            mcp_servers=[grocery_server],
            model_settings=ModelSettings(tool_choice="auto"),
            mcp_config={
                "convert_schemas_to_strict": True,
                "include_server_in_tool_names": True,
            },
        )

        result = await Runner.run(agent, user_request)
        return result.final_output


async def async_main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    request = " ".join(args.request).strip() or DEFAULT_REQUEST

    print(f"Using OpenAI agent model: {args.model}")
    print(f"Using MCP URL: {args.mcp_url}")
    print()

    final_output = await run_agent(
        request,
        model=args.model,
        mcp_url=args.mcp_url,
        timeout=args.timeout,
    )
    print(final_output)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
