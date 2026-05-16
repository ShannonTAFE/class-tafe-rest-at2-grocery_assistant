from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    list_intake_history,
    list_intake_items,
    to_json,
)


def register_intake_resources(mcp: FastMCP) -> None:
    @mcp.resource("grocery://intake/history")
    def intake_history_resource() -> str:
        """
        User meal and eating history.

        This resource stores one row per eating event, such as breakfast,
        lunch, dinner, snacks, takeaway meals, restaurant meals, or homemade meals.
        """
        return to_json(list_intake_history())

    @mcp.resource("grocery://intake/items")
    def intake_items_resource() -> str:
        """
        Food items and components recorded inside each intake event.

        This grouped URI is preferred for Version 1.1 and later.
        """
        return to_json(list_intake_items())

    @mcp.resource("grocery://intake-items")
    def intake_items_legacy_resource() -> str:
        """
        Legacy alias for grocery://intake/items.

        Kept temporarily so existing documentation or client calls do not break.
        """
        return to_json(list_intake_items())
