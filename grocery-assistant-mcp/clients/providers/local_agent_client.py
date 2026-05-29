"""Local LLM provider agent client for the Grocery Assistant MCP server.

This client uses an OpenAI-compatible local API, such as Ollama. It exposes the
same terminal-facing shape as the OpenAI/Gemini clients, but local tool-calling
quality depends on the selected local model.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import Client as MCPClient
from openai import OpenAI

from clients.shared.cli import add_common_agent_args, request_from_args
from clients.shared.config import DEFAULT_LOCAL_LLM_BASE_URL, DEFAULT_LOCAL_LLM_MODEL
from clients.shared.instructions import grocery_agent_instructions
from clients.shared.mcp_helpers import call_mcp_tool_checked, filter_mcp_tools
from clients.shared.schema_adapters import to_openai_chat_tools
from clients.shared.tool_logging import print_mcp_connection, print_run_header

PROVIDER_NAME = "Local LLM"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local OpenAI-compatible Grocery Assistant MCP agent client."
    )
    add_common_agent_args(
        parser,
        default_model_env="LOCAL_LLM_MODEL",
        default_model=DEFAULT_LOCAL_LLM_MODEL,
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("LOCAL_LLM_BASE_URL", DEFAULT_LOCAL_LLM_BASE_URL),
        help="OpenAI-compatible local API base URL, for example Ollama.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("LOCAL_LLM_API_KEY", "ollama"),
        help="API key for local OpenAI-compatible API. Ollama accepts a dummy value.",
    )
    return parser


def _parse_tool_args(raw_arguments: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _message_tool_calls_for_history(tool_calls: Any) -> list[dict[str, Any]]:
    history_calls: list[dict[str, Any]] = []
    for tool_call in tool_calls or []:
        function = getattr(tool_call, "function", None)
        history_calls.append(
            {
                "id": getattr(tool_call, "id", ""),
                "type": "function",
                "function": {
                    "name": getattr(function, "name", ""),
                    "arguments": getattr(function, "arguments", "{}"),
                },
            }
        )
    return history_calls


async def run_agent(
    user_request: str,
    *,
    model: str,
    base_url: str,
    api_key: str,
    mcp_url: str,
    timeout: float,
    allow_writes: bool,
    max_tool_rounds: int = 4,
    max_result_chars: int = 8000,
) -> str:
    """Run one local OpenAI-compatible tool-calling request against MCP."""

    local_client = OpenAI(base_url=base_url, api_key=api_key)

    async with MCPClient(mcp_url) as mcp_client:
        await mcp_client.ping()
        mcp_tools = filter_mcp_tools(await mcp_client.list_tools(), allow_writes=allow_writes)
        print_mcp_connection([tool.name for tool in mcp_tools])

        tools = to_openai_chat_tools(mcp_tools)
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": grocery_agent_instructions(
                    provider_name=PROVIDER_NAME,
                    allow_writes=allow_writes,
                ),
            },
            {"role": "user", "content": user_request},
        ]

        for _round in range(max_tool_rounds):
            try:
                response = local_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.3,
                )
            except TypeError as exc:
                raise RuntimeError(
                    "The selected local/OpenAI-compatible endpoint did not accept the tools/tool_choice "
                    "arguments. Try a tool-capable local model or use a simple prompt-only local client."
                ) from exc

            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                return message.content or ""

            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": _message_tool_calls_for_history(tool_calls),
                }
            )

            for tool_call in tool_calls:
                function = getattr(tool_call, "function", None)
                tool_name = getattr(function, "name", "")
                raw_arguments = getattr(function, "arguments", "{}")
                tool_args = _parse_tool_args(raw_arguments)

                compact_result = await call_mcp_tool_checked(
                    mcp_client,
                    tool_name,
                    tool_args,
                    provider_name=PROVIDER_NAME,
                    allow_writes=allow_writes,
                    max_result_chars=max_result_chars,
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": getattr(tool_call, "id", ""),
                        "name": tool_name,
                        "content": compact_result,
                    }
                )

        return (
            "Stopped after reaching the maximum tool-call rounds. "
            "Try a narrower request, increase --max-tool-rounds, or use the OpenAI provider client."
        )


async def async_main() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    request = request_from_args(args.request)

    print_run_header(
        provider_name=PROVIDER_NAME,
        model=args.model,
        mcp_url=args.mcp_url,
        allow_writes=args.allow_writes,
    )
    print(f"Local base URL: {args.base_url}")
    print()

    final_output = await run_agent(
        request,
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        mcp_url=args.mcp_url,
        timeout=args.timeout,
        allow_writes=args.allow_writes,
        max_tool_rounds=args.max_tool_rounds,
        max_result_chars=args.max_result_chars,
    )
    print(final_output)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
