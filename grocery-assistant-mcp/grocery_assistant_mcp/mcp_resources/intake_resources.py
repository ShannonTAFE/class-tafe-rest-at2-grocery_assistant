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

        It is separated from intake item details so the assistant can summarise
        meals at a high level without needing to inspect every ingredient.
        """
        return to_json(list_intake_history())
    

    @mcp.resource("grocery://intake-items")
    def intake_items_resource() -> str:
        """
        Food items and components recorded inside each intake event.

        This resource stores the individual ingredients or meal components linked
        to an intake history record by intake_id.

        Keeping intake items separate allows one meal to contain multiple foods,
        supports nutrition estimates per component, and allows optional linking
        back to inventory stock_id records.
        """
        return to_json(list_intake_items())