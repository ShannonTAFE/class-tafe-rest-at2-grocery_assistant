from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    list_inventory_consumption,
    to_json,
)


def register_inventory_consumption_resources(mcp: FastMCP) -> None:
    """Register inventory consumption resources with the MCP server."""

    @mcp.resource("grocery://inventory-consumption")
    def inventory_consumption_resource() -> str:
        """
        Return inventory consumption event records as JSON text.

        This resource records stock usage events, including inventory-only
        consumption and intake-linked consumption. It explains why inventory
        quantities changed over time.
        """
        return to_json(list_inventory_consumption())