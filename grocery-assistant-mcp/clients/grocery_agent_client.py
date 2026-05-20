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
You are a grocery planning assistant connected to the user's Grocery Assistant MCP server.

Use the MCP tools to inspect inventory, intake, planning signals, meal suggestions,
restock suggestions, and recommendation drafts.

Important behaviour:
- Prefer read/review/draft tools before write tools.
- Do not modify inventory or intake unless the user clearly asks for a change.
- Treat recommendation outputs as decision support, not final truth.
- Explain which tool results influenced your answer.
- Respect data quality warnings, low confidence signals, and missing expiry data.
- When suggesting meals, consider inventory availability, use-soon items, low-stock items,
  and reasonable missing-ingredient flexibility.
- When suggesting restocks, distinguish urgent staples from optional or preference-based items.
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
        request = "Review my current inventory and suggest useful next actions."

    asyncio.run(run_agent(request))