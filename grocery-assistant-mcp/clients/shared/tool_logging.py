"""Small terminal logging helpers for interpretable client runs."""

from __future__ import annotations

import json
from typing import Any


def print_run_header(*, provider_name: str, model: str, mcp_url: str, allow_writes: bool) -> None:
    print(f"Provider: {provider_name}")
    print(f"Model: {model}")
    print(f"MCP URL: {mcp_url}")
    print(f"Write tools enabled: {allow_writes}")
    print()


def print_mcp_connection(tool_names: list[str]) -> None:
    print("Connected to Grocery MCP server.")
    print(f"Visible client tools: {len(tool_names)}")
    for name in tool_names:
        print(f"- {name}")
    print()


def print_tool_call(*, provider_name: str, tool_name: str, tool_args: dict[str, Any]) -> None:
    print("\n" + "=" * 72)
    print(f"{provider_name.upper()} MCP TOOL CALL")
    print("=" * 72)
    print(f"Tool: {tool_name}")
    print("Arguments:")
    print(json.dumps(tool_args, indent=2, ensure_ascii=False))
    print("=" * 72)


def print_tool_result_summary(*, tool_name: str, compact_result: str, max_preview_chars: int = 700) -> None:
    preview = compact_result[:max_preview_chars]
    if len(compact_result) > max_preview_chars:
        preview += "\n... [preview truncated]"
    print(f"\nTool result preview for {tool_name}:")
    print(preview)
    print()
