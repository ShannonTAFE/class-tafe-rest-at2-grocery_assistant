from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_tools.inventory_tools import (
    register_inventory_tools,
)
from grocery_assistant_mcp.mcp_tools.intake_tools import (
    register_intake_tools,
)


def register_tools(mcp: FastMCP) -> None:
    """
    Register all MCP tools.
    """

    register_inventory_tools(mcp)
    register_intake_tools(mcp)