from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import Optional

from grocery_assistant_mcp.core import grocery_service
from grocery_assistant_mcp.core.grocery_service import (
    add_inventory_item as add_inventory_item_service,
    update_inventory_item as update_inventory_item_service,
    remove_inventory_item as remove_inventory_item_service,

)


def register_inventory_tools(mcp: FastMCP) -> None:
    """
    Register inventory-related MCP tools.
    """

    @mcp.tool()
    def search_inventory(
        query: Annotated[
            str,
            Field(
                description=(
                    "Optional text search across inventory item name, brand, and notes. "
                    'Use this for searches like "chicken", "oats", "pasta", or "use soon". '
                    "Leave blank when filtering only by category or location."
                )
            ),
        ] = "",
        category: Annotated[
            str,
            Field(
                description=(
                    "Optional inventory category filter. Use broad categories such as "
                    '"pantry", "protein", "dairy", "vegetable", "fruit", or "snack". '
                    "Leave blank if category is not needed."
                )
            ),
        ] = "",
        location: Annotated[
            str,
            Field(
                description=(
                    "Optional storage location filter. Use locations such as "
                    '"cupboard", "fridge", "freezer", or "pantry". '
                    "Leave blank if location is not needed."
                )
            ),
        ] = "",
    ) -> list[dict]:
        """
        Search the current grocery inventory.

        Use this tool when the user asks whether a specific food item is available,
        wants to find items in a category, or wants to check items stored in a
        particular location.

        This is a read-only tool. It does not add, update, remove, or consume
        inventory items.

        Returns matching inventory rows from user_inventory.csv.
        """
        return grocery_service.search_inventory(
            query=query,
            category=category,
            location=location,
        )

    @mcp.tool()
    def add_inventory_item(
        food_item: Annotated[
            str,
            Field(description='Name of the food item to add. Required. Example: "Rolled oats".'),
        ],
        brand: Annotated[
            str,
            Field(description='Brand name if known. Leave blank if unknown. Example: "Uncle Tobys".'),
        ] = "",
        category: Annotated[
            str,
            Field(description='Broad food category. Example: "pantry", "protein", "dairy", "vegetable", "fruit".'),
        ] = "",
        location: Annotated[
            str,
            Field(description='Storage location. Example: "cupboard", "fridge", "freezer", "pantry".'),
        ] = "",
        quantity: Annotated[
            float,
            Field(description='Numeric amount of the item. Use with unit. Example: 1 for one bag, 500 for 500 g.'),
        ] = 0,
        unit: Annotated[
            str,
            Field(description='Unit for quantity. Example: "bag", "packet", "g", "kg", "can", "item".'),
        ] = "",
        servings_remaining: Annotated[
            float,
            Field(description='Estimated number of usable servings remaining. Example: 10.'),
        ] = 0,
        stock_status: Annotated[
            str,
            Field(description='Current inventory status. Use "ok", "low", "empty", "used", "expired", or "removed".'),
        ] = "ok",
        expiry_date: Annotated[
            str,
            Field(description='Expiry or use-by date in YYYY-MM-DD format. Leave blank if unknown.'),
        ] = "",
        notes: Annotated[
            str,
            Field(description='Optional notes about the item. Example: "Use soon" or "Added during grocery shop".'),
        ] = "",
    ) -> dict:
        """
        Add one new grocery inventory item.

        Use this when the user wants to record a new grocery item that is not
        already represented in the inventory.

        This tool creates a new inventory row and the service layer generates
        the stock_id internally.

        Do not use this tool to update an existing item, reduce servings, mark
        an item as consumed, or correct an existing inventory row.
        """
        return add_inventory_item_service(
            food_item=food_item,
            brand=brand,
            category=category,
            location=location,
            quantity=quantity,
            unit=unit,
            servings_remaining=servings_remaining,
            stock_status=stock_status,
            expiry_date=expiry_date,
            notes=notes,
        )
    @mcp.tool()
    def update_inventory_item(
        stock_id: str,
        food_item: str | None = None,
        brand: str | None = None,
        category: str | None = None,
        location: str | None = None,
        quantity: float | None = None,
        unit: str | None = None,
        servings_remaining: float | None = None,
        stock_status: str | None = None,
        expiry_date: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """
        Update an existing inventory item by stock_id.

        Only fields provided by the caller are updated.
        Fields left as None are not changed.

        Use this tool when the user wants to:
        - correct an inventory item
        - change quantity or servings remaining
        - update stock status
        - update expiry date
        - move an item to a different location
        - add or clear notes
        """

        return update_inventory_item_service(
            stock_id=stock_id,
            food_item=food_item,
            brand=brand,
            category=category,
            location=location,
            quantity=quantity,
            unit=unit,
            servings_remaining=servings_remaining,
            stock_status=stock_status,
            expiry_date=expiry_date,
            notes=notes,
        )
    @mcp.tool()
    def remove_inventory_item(
        stock_id: str,
        removal_type: str = "unknown",
        removal_reason: str = "",
        quantity_wasted: Optional[float] = None,
        servings_wasted: Optional[float] = None,
        tracking_confidence: str = "medium",
        notes: str = "",
    ) -> dict:
        """
        Remove an item from active inventory.

        Use this when the user says an item should leave active inventory,
        including when it was used up, expired, spoiled, discarded, duplicated,
        incorrectly added, or no longer available.

        This tool records a food waste entry only when removal_type is one of:
        - expired
        - spoiled
        - discarded
        - unused
        - overbought
        - did_not_like

        This tool does not record food waste when removal_type is one of:
        - used_up
        - duplicate_entry
        - incorrect_entry
        - test_entry
        - unknown

        If quantity_wasted or servings_wasted are not supplied for a waste-type
        removal, the service uses the item's current remaining quantity and
        servings as the estimated wasted amount.
        """
        return remove_inventory_item_service(
            stock_id=stock_id,
            removal_type=removal_type,
            removal_reason=removal_reason,
            quantity_wasted=quantity_wasted,
            servings_wasted=servings_wasted,
            tracking_confidence=tracking_confidence,
            notes=notes,
        )
