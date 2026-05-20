from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_tools.inventory_tools import (
    register_inventory_tools,
)
from grocery_assistant_mcp.mcp_tools.intake_tools import (
    register_intake_tools,
)
from grocery_assistant_mcp.mcp_tools.consumption_tools import (
    register_consumption_tools,
)

from grocery_assistant_mcp.mcp_tools.batch_meal_tools import (
    register_batch_meal_tools,
)

from grocery_assistant_mcp.mcp_tools.planning_tools import (
    register_planning_tools,
)

from grocery_assistant_mcp.mcp_tools.meal_suggestion_tools import (
    register_meal_suggestion_tools,
)

def register_tools(mcp: FastMCP) -> None:
    """
    Register all MCP tools.
    """

    register_inventory_tools(mcp)
    register_intake_tools(mcp)
    register_consumption_tools(mcp)
    register_batch_meal_tools(mcp)
    register_planning_tools(mcp)
    register_meal_suggestion_tools(mcp)