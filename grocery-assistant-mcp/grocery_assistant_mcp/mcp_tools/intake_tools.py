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