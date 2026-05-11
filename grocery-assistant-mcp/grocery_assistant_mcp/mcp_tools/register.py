from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_tools.inventory_tools import register_inventory_tools


def register_tools(mcp: FastMCP) -> None:
    """
    Register all MCP tools.
    """

    register_inventory_tools(mcp)