from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_resources.register import register_resources
from grocery_assistant_mcp.mcp_tools.register import register_tools
from grocery_assistant_mcp.mcp_prompts.register import register_prompts
from grocery_assistant_mcp.utils.logging_config import configure_logging


def create_mcp_server(
    host: str = "127.0.0.1",
    port: int = 8000,
) -> FastMCP:
    """
    Creates and configures the Grocery Assistant MCP server.

    Shared by:
    - stdio_server.py
    - streamable_http_server.py
    """

    configure_logging()

    mcp = FastMCP(
        "Grocery Assistant",
        host=host,
        port=port,
    )

    register_resources(mcp)
    register_tools(mcp)
    register_prompts(mcp)

    return mcp