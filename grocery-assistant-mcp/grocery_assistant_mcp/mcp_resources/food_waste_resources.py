from __future__ import annotations

"""
Food waste MCP resources.

These resources expose records from user_food_waste.csv.

The food waste CSV is used for grocery-learning events, not general deletion
history. It records meaningful waste outcomes that may help future tools and
prompts provide better grocery planning, shopping, and waste-reduction advice.
"""

from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    list_food_waste_items,
    to_json,
)

def register_food_waste_resources(mcp: FastMCP) -> None:
    """Register food waste resources with the MCP server."""

    @mcp.resource("grocery://food-waste")
    def food_waste_resource() -> str:
        """
        Return behaviour-relevant food waste records as JSON text.

        This resource is separate from grocery://inventory because waste
        records serve a learning purpose, not a current stock tracking purpose.

        It records meaningful waste outcomes such as expired, spoiled,
        discarded, unused, overbought, or disliked food. These records can help
        future tools and prompts identify waste patterns, shopping quantity
        issues, and foods that may need better meal planning.

        It is not a general log of every out-of-stock or used-up item.
        Normal used-up items may remain in grocery://inventory as out-of-stock
        tracked items if they are useful for shopping or personalization.
        """
        return to_json(list_food_waste_items())

    @mcp.resource("grocery://food-waste/expired")
    def expired_food_waste_resource() -> str:
        """
        Return food waste records where the waste type is expired.

        This resource focuses on items that were removed from active inventory
        because they expired before being fully used. It can help identify
        repeated expiry patterns, short shelf-life items, or groceries that may
        need to be bought in smaller quantities or planned into meals earlier.
        """
        return to_json(list_food_waste_items(waste_type="expired"))