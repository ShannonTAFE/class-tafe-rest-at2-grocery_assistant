import asyncio
import os
import sys
from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings


load_dotenv()

MCP_URL = os.getenv("GROCERY_MCP_URL", "http://127.0.0.1:8000/mcp")


GROCERY_AGENT_INSTRUCTIONS = """
WRITE SAFETY:
- Never call add, update, remove, or consume tools unless the user explicitly asks to change stored data.
- If the user asks for advice, review, suggestions, planning, or recommendations, use read/review/draft tools only.
- Before using a write tool, briefly state the intended change in the final response after the tool call.
- If the user request is ambiguous, prefer explaining what could be changed rather than changing data.
- Removal tools are destructive. Only use remove tools when the user clearly asks to delete/remove a record.
"""


async def run_agent(user_request: str) -> None:
    async with MCPServerStreamableHttp(
        name="Grocery Assistant MCP",
        params={
            "url": MCP_URL,
            "timeout": 30,
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    ) as grocery_server:
        agent = Agent(
            name="Grocery Assistant Agent",
            instructions=GROCERY_AGENT_INSTRUCTIONS,
            mcp_servers=[grocery_server],
            model_settings=ModelSettings(
                tool_choice="auto",
            ),
            mcp_config={
                "convert_schemas_to_strict": True,
                "include_server_in_tool_names": True,
            },
        )

        result = await Runner.run(agent, user_request)
        print(result.final_output)


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]).strip()

    if not request:
        request = "Review my current grocery planning context and suggest useful next actions."

    asyncio.run(run_agent(request))