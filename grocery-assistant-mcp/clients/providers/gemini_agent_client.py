"""Gemini provider agent client for the Grocery Assistant MCP server.

This client uses Gemini function calling plus a small shared MCP tool loop. It is
intended as a free/low-cost comparison path with the same terminal-facing shape
as the OpenAI provider client.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import Client
from google import genai
from google.genai import types

from clients.shared.cli import add_common_agent_args, request_from_args
from clients.shared.config import DEFAULT_GEMINI_MODEL
from clients.shared.instructions import grocery_agent_instructions
from clients.shared.mcp_helpers import (
    call_mcp_tool_checked,
    filter_mcp_tools,
)
from clients.shared.schema_adapters import to_gemini_tools
from clients.shared.tool_logging import print_mcp_connection, print_run_header

PROVIDER_NAME = "Gemini"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Gemini Grocery Assistant MCP agent client."
    )
    return add_common_agent_args(
        parser,
        default_model_env="GEMINI_MODEL",
        default_model=DEFAULT_GEMINI_MODEL,
    )


def extract_text(response: Any) -> str:
    """Extract plain text from a Gemini response."""

    text = getattr(response, "text", None)
    if text:
        return text

    parts: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                parts.append(part_text)
    return "\n".join(parts).strip()


def extract_function_calls(response: Any) -> list[Any]:
    """Extract Gemini function-call parts from a response."""

    calls: list[Any] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            function_call = getattr(part, "function_call", None)
            if function_call:
                calls.append(function_call)
    return calls


async def run_agent(
    user_request: str,
    *,
    model: str,
    mcp_url: str,
    timeout: float,
    allow_writes: bool,
    max_tool_rounds: int = 4,
    max_result_chars: int = 8000,
) -> str:
    """Run one Gemini function-calling agent request against the MCP server."""

    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    gemini_client = genai.Client()

    async with Client(mcp_url) as mcp_client:
        await mcp_client.ping()
        mcp_tools = filter_mcp_tools(await mcp_client.list_tools(), allow_writes=allow_writes)
        print_mcp_connection([tool.name for tool in mcp_tools])

        gemini_tools = to_gemini_tools(mcp_tools)
        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part(text=user_request)])
        ]
        config = types.GenerateContentConfig(
            system_instruction=grocery_agent_instructions(
                provider_name=PROVIDER_NAME,
                allow_writes=allow_writes,
            ),
            tools=gemini_tools,
            temperature=0.3,
        )

        response = gemini_client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        for _round in range(max_tool_rounds):
            function_calls = extract_function_calls(response)
            if not function_calls:
                return extract_text(response)

            for function_call in function_calls:
                tool_name = str(function_call.name)
                tool_args = dict(function_call.args or {})
                compact_result = await call_mcp_tool_checked(
                    mcp_client,
                    tool_name,
                    tool_args,
                    provider_name=PROVIDER_NAME,
                    allow_writes=allow_writes,
                    max_result_chars=max_result_chars,
                )

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
                                    response={"result": compact_result},
                                )
                            )
                        ],
                    )
                )

            response = gemini_client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

        return (
            "Stopped after reaching the maximum tool-call rounds. "
            "Try a narrower request or increase --max-tool-rounds."
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

    final_output = await run_agent(
        request,
        model=args.model,
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
