from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    list_inventory_items,
    to_json,
)


def register_inventory_resources(mcp: FastMCP) -> None:
    """Register tracked inventory resources with the MCP server."""

    @mcp.resource("grocery://inventory")
    def inventory_resource() -> str:
        """
        Return the user's tracked grocery inventory as JSON text.

        This resource represents grocery items that are useful for current or
        future decisions. It may include available items, low-stock items,
        out-of-stock items kept as shopping reminders, and expired items still
        physically present.

        Out-of-stock records are intentionally allowed because they can help
        the assistant learn which foods are common staples, which items are
        frequently used, and which past purchases are low-priority to restock.

        This resource should not contain meaningful food waste history.
        Waste-related removals are stored separately in grocery://food-waste.
        """
        return to_json(list_inventory_items())