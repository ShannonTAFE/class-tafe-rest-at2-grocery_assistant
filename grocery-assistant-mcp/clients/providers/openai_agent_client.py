"""OpenAI provider agent client for the Grocery Assistant MCP server.

This is the primary paid/provider-quality path. It uses the OpenAI Agents SDK to
connect directly to the running Grocery Assistant MCP server.
"""

from __future__ import annotations

import argparse
import asyncio

from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings

from clients.shared.cli import add_common_agent_args, request_from_args
from clients.shared.config import DEFAULT_OPENAI_AGENT_MODEL
from clients.shared.instructions import grocery_agent_instructions
from clients.shared.openai_agents_filter import build_static_tool_filter
from clients.shared.tool_logging import print_run_header

PROVIDER_NAME = "OpenAI"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the OpenAI Grocery Assistant MCP agent client."
    )
    return add_common_agent_args(
        parser,
        default_model_env="OPENAI_AGENT_MODEL",
        default_model=DEFAULT_OPENAI_AGENT_MODEL,
    )


async def run_agent(
    user_request: str,
    *,
    model: str,
    mcp_url: str,
    timeout: float,
    allow_writes: bool,
) -> str:
    """Run one OpenAI agent request against the Grocery MCP server."""

    async with MCPServerStreamableHttp(
        name="Grocery Assistant MCP",
        params={"url": mcp_url, "timeout": timeout},
        cache_tools_list=True,
        max_retry_attempts=3,
        tool_filter=build_static_tool_filter(allow_writes=allow_writes),
        # Use normal SDK text behavior. The project can enable structured content
        # later if duplication in tool output is fully understood.
        use_structured_content=False,
    ) as grocery_server:
        agent = Agent(
            name="Grocery Assistant Agent",
            instructions=grocery_agent_instructions(
                provider_name=PROVIDER_NAME,
                allow_writes=allow_writes,
            ),
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
    )
    print(final_output)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
