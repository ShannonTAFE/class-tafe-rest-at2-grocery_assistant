from mcp.server.fastmcp import FastMCP

from mcp_resources.register import register_resources
from mcp_tools.register import register_tools
from mcp_prompts.register import register_prompts
from utils.logging_config import configure_logging


def create_mcp_server() -> FastMCP:
    configure_logging()

    mcp = FastMCP("Grocery Assistant")

    register_resources(mcp)
    register_tools(mcp)
    register_prompts(mcp)

    return mcp


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run()