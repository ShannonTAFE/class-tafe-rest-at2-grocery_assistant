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
    """Register food waste resources with the MCP server.

    Food waste records are stored separately from active inventory so the
    inventory resource can remain focused on food currently available to use.

    This resource is intended for behaviour-relevant waste tracking, not
    general inventory deletion logs. It supports future personalization by
    recording items that were expired, spoiled, discarded, unused, overbought,
    or disliked.
    """

    @mcp.resource("grocery://food-waste")
    def food_waste_resource() -> str:
        """
        Return all food waste records as JSON text.

        This resource provides a history of meaningful food waste events.
        It is used to review patterns such as repeated expiry, spoiled food,
        overbuying, disliked items, or food discarded before being fully used.

        These records can support future prompts and tools that help the user:
        - reduce repeat waste
        - improve shopping quantities
        - identify foods that are not being used in time
        - compare initial supply, estimated consumption, and leftover waste

        This resource should not be used for normal active inventory.
        Use grocery://inventory for current available stock.
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