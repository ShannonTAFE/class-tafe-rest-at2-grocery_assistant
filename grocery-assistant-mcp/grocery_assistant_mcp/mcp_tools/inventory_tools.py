from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core import grocery_service


def register_inventory_tools(mcp: FastMCP) -> None:
    """
    Register inventory-related MCP tools.
    """

    @mcp.tool()
    def search_inventory(
        query: str = "",
        category: str = "",
        location: str = "",
    ) -> list[dict]:
        """
        Search the user's grocery inventory by food name, category, or location.
        """

        return grocery_service.search_inventory(
            query=query,
            category=category,
            location=location,
        )