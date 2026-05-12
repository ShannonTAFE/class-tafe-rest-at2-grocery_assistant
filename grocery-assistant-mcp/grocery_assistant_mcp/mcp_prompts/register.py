from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_prompts.inventory_prompts import (
    register_inventory_prompts,
)
from grocery_assistant_mcp.mcp_prompts.intake_prompts import (
    register_intake_prompts,
)


def register_prompts(mcp: FastMCP) -> None:
    """
    Register all Grocery Assistant MCP prompts.
    """

    register_inventory_prompts(mcp)
    register_intake_prompts(mcp)