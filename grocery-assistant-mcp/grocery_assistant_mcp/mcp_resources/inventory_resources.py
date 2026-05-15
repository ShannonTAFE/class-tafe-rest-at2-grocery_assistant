from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    list_inventory_items,
    to_json,
)


def register_inventory_resources(mcp: FastMCP) -> None:

    @mcp.resource("grocery://inventory")
    def inventory_resource() -> str:
        """Current grocery inventory."""
        return to_json(list_inventory_items())