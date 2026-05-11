from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core import grocery_service


def register_intake_tools(mcp: FastMCP) -> None:
    """
    Register intake-related MCP tools.
    """

    @mcp.tool()
    def get_recent_intake(
        days_back: int = 7,
        meal_type: str = "",
    ) -> list[dict]:
        """
        Get recent food intake records from the user's intake history.

        Args:
            days_back: Number of days back from today to include.
            meal_type: Optional filter such as breakfast, lunch, dinner, or snack.

        Returns:
            A list of recent intake history records, newest first.
        """

        return grocery_service.get_recent_intake(
            days_back=days_back,
            meal_type=meal_type,
        )
    @mcp.tool()
    def get_daily_intake_summary(date: str) -> dict:
        """
        Get all logged meals, food items, and calculated nutrition totals
        for a specific date.

        Args:
            date: Date to summarise in YYYY-MM-DD format.

        Returns:
            A dictionary containing:
            - date
            - meal_count
            - item_count
            - meals
            - items
            - nutrition_totals
            - missing_nutrition_counts
        """

        return grocery_service.get_daily_intake_summary(date=date)