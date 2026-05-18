from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from grocery_assistant_mcp.core.grocery_service import (
    add_meal_with_items as add_meal_with_items_service,
)


def register_batch_meal_tools(mcp: FastMCP) -> None:
    """
    Register batch meal logging tools.

    These tools create structured intake records but do not deduct inventory.
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

        Use this when a user describes a meal with multiple components.

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

        If inventory should be deducted, use an explicit inventory consumption
        workflow instead.
        """
        return add_meal_with_items_service(
            meal_data=meal_data,
            items=items,
        )