from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.mcp_resources.inventory_resources import (
    register_inventory_resources,
)
from grocery_assistant_mcp.mcp_resources.intake_resources import (
    register_intake_resources,
)
from grocery_assistant_mcp.mcp_resources.food_waste_resources import (
    register_food_waste_resources,
)

def register_resources(mcp: FastMCP) -> None:
    register_inventory_resources(mcp)
    register_intake_resources(mcp)
    register_food_waste_resources(mcp)