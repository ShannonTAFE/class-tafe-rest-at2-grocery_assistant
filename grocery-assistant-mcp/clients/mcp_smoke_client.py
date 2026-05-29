"""Deterministic MCP smoke client for the Grocery Assistant MCP server.

This file intentionally does not use an LLM. It proves Python can connect to the
MCP server, list tools, and call a known safe tool.
"""

from __future__ import annotations

import argparse
import asyncio

from dotenv import load_dotenv
from fastmcp import Client

from clients.shared.config import DEFAULT_MCP_URL, env_str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a deterministic Grocery MCP smoke test.")
    parser.add_argument(
        "--mcp-url",
        default=env_str("GROCERY_MCP_URL", DEFAULT_MCP_URL),
        help="Grocery MCP Streamable HTTP URL.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of inventory rows to preview.",
    )
    parser.add_argument(
        "--show-resources",
        action="store_true",
        help="Also list visible MCP resources if the server supports resource listing.",
    )
    parser.add_argument(
        "--show-prompts",
        action="store_true",
        help="Also list visible MCP prompts if the server supports prompt listing.",
    )
    return parser


async def run_smoke_test(*, mcp_url: str, limit: int, show_resources: bool, show_prompts: bool) -> None:
    async with Client(mcp_url) as client:
        await client.ping()
        print("Connected to Grocery MCP server.")

        tools = await client.list_tools()
        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool.name}")

        if show_resources:
            try:
                resources = await client.list_resources()
                print("\nAvailable resources:")
                for resource in resources:
                    print(f"- {resource.uri}")
            except Exception as exc:  # pragma: no cover - depends on server capability
                print(f"\nResource listing unavailable: {exc}")

        if show_prompts:
            try:
                prompts = await client.list_prompts()
                print("\nAvailable prompts:")
                for prompt in prompts:
                    print(f"- {prompt.name}")
            except Exception as exc:  # pragma: no cover - depends on server capability
                print(f"\nPrompt listing unavailable: {exc}")

        result = await client.call_tool(
            "search_inventory",
            {"query": "", "category": "", "location": ""},
        )

        structured = getattr(result, "structured_content", {}) or {}
        items = structured.get("result", []) if isinstance(structured, dict) else []

        print("\nsearch_inventory summary:")
        print(f"- Returned {len(items)} inventory item(s)")

        for item in items[:limit]:
            print(
                f"- {item.get('stock_id')}: "
                f"{item.get('food_item')} "
                f"({item.get('stock_status')})"
            )


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    asyncio.run(
        run_smoke_test(
            mcp_url=args.mcp_url,
            limit=args.limit,
            show_resources=args.show_resources,
            show_prompts=args.show_prompts,
        )
    )


if __name__ == "__main__":
    main()
