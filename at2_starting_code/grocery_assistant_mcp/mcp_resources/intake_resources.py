from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    read_intake_history,
    read_intake_items,
    df_to_records,
    to_json,
)


def register_intake_resources(mcp: FastMCP) -> None:

    @mcp.resource("grocery://intake-history")
    def intake_history_resource() -> str:
        """Meal-level food intake history."""
        return to_json(df_to_records(read_intake_history()))

    @mcp.resource("grocery://intake-items")
    def intake_items_resource() -> str:
        """Ingredient-level or component-level intake records."""
        return to_json(df_to_records(read_intake_items()))