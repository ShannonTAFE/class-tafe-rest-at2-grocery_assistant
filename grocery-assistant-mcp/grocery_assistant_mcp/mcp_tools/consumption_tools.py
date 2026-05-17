from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grocery_assistant_mcp.core.grocery_service import (
    add_intake_item_from_inventory as add_intake_item_from_inventory_service,
    consume_inventory_item as consume_inventory_item_service,
)


def register_consumption_tools(mcp: FastMCP) -> None:
    """
    Register controlled inventory consumption tools.

    These tools sit between inventory and intake workflows.

    The MCP layer stays thin:
    - validation happens in grocery_service.py
    - inventory deduction logic happens in grocery_service.py
    - CSV backup/write logic happens in grocery_service.py
    - this file only exposes controlled service functions as MCP tools
    """

    @mcp.tool()
    def consume_inventory_item(
        stock_id: Annotated[
            str,
            Field(
                description=(
                    "Required inventory stock ID to consume from. "
                    'Example: "inv_001". Use search_inventory first if the ID is unknown.'
                )
            ),
        ],
        quantity_used: Annotated[
            float,
            Field(
                description=(
                    "Optional physical quantity consumed from inventory. "
                    "Use with the inventory item's unit. "
                    'Example: 100 when using 100 g. Use 0 if tracking servings only.'
                )
            ),
        ] = 0,
        servings_used: Annotated[
            float,
            Field(
                description=(
                    "Optional number of servings consumed from inventory. "
                    'Example: 1 for one serving. Use 0 if tracking quantity only.'
                )
            ),
        ] = 0,
        usage_reason: Annotated[
            str,
            Field(
                description=(
                    "Optional reason for consumption. "
                    'Examples: "consumed", "used in cooking", "finished item".'
                )
            ),
        ] = "consumed",
        notes: Annotated[
            str,
            Field(
                description=(
                    "Optional notes about the consumption event, uncertainty, "
                    "or how the item was used."
                )
            ),
        ] = "",
    ) -> dict:
        """
        Consume part or all of a tracked inventory item.

        Use this when the user says they used, ate, finished, or reduced a
        grocery inventory item but does not want to create an intake item.

        This tool updates inventory only.

        It does not:
        - create a meal entry
        - create an intake item
        - remove the inventory row
        - create a food waste record

        If the item reaches zero quantity and zero servings, it remains in
        inventory with stock_status set to "out" so it can still support
        restock reminders and grocery personalization.
        """
        return consume_inventory_item_service(
            stock_id=stock_id,
            quantity_used=quantity_used,
            servings_used=servings_used,
            usage_reason=usage_reason,
            notes=notes,
        )

    @mcp.tool()
    def add_intake_item_from_inventory(
        intake_id: Annotated[
            str,
            Field(
                description=(
                    "Required parent intake entry ID to attach this food item to. "
                    'Example: "intake_001". Use search_intake first if the ID is unknown.'
                )
            ),
        ],
        stock_id: Annotated[
            str,
            Field(
                description=(
                    "Required inventory stock ID being eaten or used. "
                    'Example: "inv_001". Use search_inventory first if the ID is unknown.'
                )
            ),
        ],
        amount_eaten: Annotated[
            str,
            Field(
                description=(
                    "Optional free-text amount eaten. "
                    'Examples: "1 serving", "100 g", "half a tub", "2 slices".'
                )
            ),
        ] = "",
        quantity_used: Annotated[
            float,
            Field(
                description=(
                    "Optional physical quantity consumed from inventory. "
                    "Use with the inventory item's unit. "
                    'Example: 100 when using 100 g. Use 0 if tracking servings only.'
                )
            ),
        ] = 0,
        servings_used: Annotated[
            float,
            Field(
                description=(
                    "Optional number of servings consumed from inventory. "
                    'Example: 1 for one serving. Use 0 if tracking quantity only.'
                )
            ),
        ] = 0,
        calories_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated calories for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        protein_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated protein in grams for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        carbs_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated carbohydrates in grams for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        fat_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated fat in grams for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        fibre_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated fibre in grams for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        sugar_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated sugar in grams for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        sodium_mg_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated sodium in milligrams for this consumed inventory item. "
                    "Use 0 if unknown."
                )
            ),
        ] = 0,
        nutrition_confidence: Annotated[
            str,
            Field(
                description=(
                    "Confidence in the nutrition estimate. "
                    "Use one of: low, medium, high, unknown."
                )
            ),
        ] = "medium",
        notes: Annotated[
            str,
            Field(
                description=(
                    "Optional notes about the inventory-linked intake item, "
                    "portion uncertainty, or how it was used."
                )
            ),
        ] = "",
    ) -> dict:
        """
        Add an intake item from a tracked inventory item and deduct inventory.

        Use this when the user ate or used a known inventory item as part of
        an existing meal or eating event.

        This tool creates a child intake item and updates inventory together.

        It copies food_item, brand, and category from the inventory row, so the
        caller should not manually provide those fields.

        It does not:
        - create the parent meal entry
        - remove the inventory row
        - create a food waste record
        - modify the parent intake entry totals automatically

        Use add_intake_entry first if the parent meal does not exist yet.
        Use add_intake_item for non-inventory food, takeaway, restaurant food,
        or historical estimates that should not deduct inventory.
        """
        return add_intake_item_from_inventory_service(
            intake_id=intake_id,
            stock_id=stock_id,
            amount_eaten=amount_eaten,
            quantity_used=quantity_used,
            servings_used=servings_used,
            calories_estimate=calories_estimate,
            protein_g_estimate=protein_g_estimate,
            carbs_g_estimate=carbs_g_estimate,
            fat_g_estimate=fat_g_estimate,
            fibre_g_estimate=fibre_g_estimate,
            sugar_g_estimate=sugar_g_estimate,
            sodium_mg_estimate=sodium_mg_estimate,
            nutrition_confidence=nutrition_confidence,
            notes=notes,
        )