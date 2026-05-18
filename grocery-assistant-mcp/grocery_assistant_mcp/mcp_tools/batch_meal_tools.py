from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grocery_assistant_mcp.core.grocery_service import (
    add_meal_with_inventory_items as add_meal_with_inventory_items_service,
    add_meal_with_items as add_meal_with_items_service,
)


def register_batch_meal_tools(mcp: FastMCP) -> None:
    """
    Register batch meal logging tools.

    Version 1.4B:
    - add_meal_with_items
    - intake-only parent + child meal logging

    Version 1.4C:
    - add_meal_with_inventory_items
    - parent + child meal logging with explicit inventory deduction
    """

    @mcp.tool()
    def add_meal_with_items(
        meal_data: Annotated[
            dict,
            Field(
                description=(
                    "Parent meal/intake entry data. Use this for the overall "
                    "meal event, such as date, time, meal_type, meal_name, "
                    "source, amount_eaten, nutrition estimates, hunger notes, "
                    "leftovers_created, and notes."
                )
            ),
        ],
        items: Annotated[
            list[dict],
            Field(
                description=(
                    "Child intake items belonging to the meal. Each item should "
                    "describe one food/component such as spaghetti, beef mince, "
                    "tomato sauce, vegetables, or toppings. Optional stock_id "
                    "values are treated as references only and do not deduct "
                    "inventory."
                )
            ),
        ],
    ) -> dict:
        """
        Add one parent meal entry and multiple child intake item rows.

        This is the Version 1.4B intake-only batch meal workflow.

        This tool writes to:
        - user_intake_history.csv
        - user_intake_items.csv

        This tool does not:
        - deduct inventory
        - create inventory consumption records
        - create food waste records
        - auto-learn meal aliases
        - auto-create meal templates
        - auto-calculate parent nutrition totals

        If inventory should be deducted, use add_meal_with_inventory_items.
        """
        return add_meal_with_items_service(
            meal_data=meal_data,
            items=items,
        )

    @mcp.tool()
    def add_meal_with_inventory_items(
        meal_data: Annotated[
            dict,
            Field(
                description=(
                    "Parent meal/intake entry data. Use this for the overall "
                    "meal event, such as date, time, meal_type, meal_name, "
                    "source, amount_eaten, nutrition estimates, hunger notes, "
                    "leftovers_created, and notes."
                )
            ),
        ],
        inventory_items: Annotated[
            list[dict],
            Field(
                description=(
                    "Inventory-linked child items that should deduct stock. "
                    "Each item must include stock_id and should include "
                    "quantity_used and/or servings_used. The inventory row is "
                    "the source of truth for food_item, brand, category, and unit."
                )
            ),
        ],
        manual_items: Annotated[
            list[dict] | None,
            Field(
                description=(
                    "Optional untracked child intake items that belong to the meal "
                    "but should not deduct inventory. These must not include stock_id. "
                    "Use this for toppings, extras, takeaway components, or items "
                    "not tracked in inventory."
                )
            ),
        ] = None,
        consumption_type: Annotated[
            str,
            Field(
                description=(
                    "Default consumption type for inventory-linked items when an "
                    "item does not provide its own consumption_type."
                )
            ),
        ] = "consumed",
        tracking_confidence: Annotated[
            str,
            Field(
                description=(
                    "Default tracking confidence for inventory-linked consumption "
                    "records when an item does not provide its own tracking_confidence."
                )
            ),
        ] = "medium",
        notes: Annotated[
            str,
            Field(
                description=(
                    "Default notes applied to inventory-linked consumption records "
                    "when an item does not provide its own notes."
                )
            ),
        ] = "",
    ) -> dict:
        """
        Add one parent meal entry, multiple child intake items, selected inventory
        deductions, and linked inventory consumption records.

        This is the Version 1.4C inventory-linked batch meal workflow.

        Use this only when the user explicitly wants inventory to be updated or
        clearly provides inventory-linked stock items.

        This tool writes to:
        - user_intake_history.csv
        - user_intake_items.csv
        - user_inventory.csv
        - user_inventory_consumption.csv

        This tool does not:
        - create food waste records
        - auto-learn meal aliases
        - auto-create meal templates
        - auto-calculate parent nutrition totals
        - perform unit conversion
        - deduct inventory for manual_items

        For ambiguous meal logging, use add_meal_with_items instead.
        """
        return add_meal_with_inventory_items_service(
            meal_data=meal_data,
            inventory_items=inventory_items,
            manual_items=manual_items,
            consumption_type=consumption_type,
            tracking_confidence=tracking_confidence,
            notes=notes,
        )