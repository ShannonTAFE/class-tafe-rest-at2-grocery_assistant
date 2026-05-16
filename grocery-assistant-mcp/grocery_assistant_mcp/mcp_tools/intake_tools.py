from mcp.server.fastmcp import FastMCP

from typing import Annotated
from pydantic import Field

from grocery_assistant_mcp.core.grocery_service import (
    add_intake_entry as add_intake_entry_service,
    add_intake_item as add_intake_item_service,
    get_daily_intake_summary as get_daily_intake_summary_service,
    get_recent_intake as get_recent_intake_service,
)


def register_intake_tools(mcp: FastMCP) -> None:
    """
    Register intake tools.

    The MCP layer stays thin:
    - validation happens in grocery_service.py
    - CSV backup/write logic happens in grocery_service.py
    - this file only exposes the service functions as MCP tools
    """

    @mcp.tool()
    def get_recent_intake(
        days_back: int = 7,
        meal_type: str = "",
    ) -> list[dict]:
        """
        Get recent food intake records from the user's intake history.
        """
        return get_recent_intake_service(days_back=days_back, meal_type=meal_type)

    @mcp.tool()
    def get_daily_intake_summary(date: str) -> dict:
        """
        Get all logged meals, food items, and calculated nutrition totals
        for a specific date in YYYY-MM-DD format.
        """
        return get_daily_intake_summary_service(date=date)

    @mcp.tool()
    def add_intake_entry(
        date: Annotated[
            str,
            Field(
                description=(
                    "Required meal date in YYYY-MM-DD format. "
                    'Example: "2026-05-16".'
                )
            ),
        ],
        meal_name: Annotated[
            str,
            Field(
                description=(
                    "Required short name of the meal or eating event. "
                    'Examples: "Spaghetti bolognese", "Toast", "Protein smoothie".'
                )
            ),
        ],
        time: Annotated[
            str,
            Field(
                description=(
                    "Optional meal time in 24-hour HH:MM format. "
                    'Example: "18:30". Leave blank if unknown.'
                )
            ),
        ] = "",
        meal_type: Annotated[
            str,
            Field(
                description=(
                    "Type of eating event. Use one of: meal, breakfast, lunch, "
                    "dinner, snack, drink, dessert, other."
                )
            ),
        ] = "meal",
        meal_description: Annotated[
            str,
            Field(
                description=(
                    "Optional longer description of what was eaten, including "
                    "important ingredients or context."
                )
            ),
        ] = "",
        source: Annotated[
            str,
            Field(
                description=(
                    "Optional source of the meal. Use values such as home, takeaway, "
                    "restaurant, cafe, work, school, friend, or other."
                )
            ),
        ] = "",
        amount_eaten: Annotated[
            str,
            Field(
                description=(
                    "Optional free-text portion description. "
                    'Examples: "1 bowl", "2 slices", "half serve", "large plate".'
                )
            ),
        ] = "",
        portion_confidence: Annotated[
            str,
            Field(
                description=(
                    "Confidence in the portion estimate. Use one of: low, medium, high."
                )
            ),
        ] = "medium",
        total_calories_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total calories for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        total_protein_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total protein in grams for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        total_carbs_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total carbohydrates in grams for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        total_fat_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total fat in grams for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        total_fibre_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total fibre in grams for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        total_sugar_g_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total sugar in grams for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        total_sodium_mg_estimate: Annotated[
            float,
            Field(
                description=(
                    "Estimated total sodium in milligrams for the meal. Use 0 if unknown."
                )
            ),
        ] = 0,
        nutrition_confidence: Annotated[
            str,
            Field(
                description=(
                    "Confidence in the nutrition estimate. Use one of: low, medium, high."
                )
            ),
        ] = "medium",
        was_finished: Annotated[
            str,
            Field(
                description=(
                    "Whether the meal was finished. Use one of: yes, no, partial, unknown."
                )
            ),
        ] = "unknown",
        leftovers_created: Annotated[
            str,
            Field(
                description=(
                    "Whether leftovers were created. Use one of: yes, no, unknown."
                )
            ),
        ] = "unknown",
        hunger_before: Annotated[
            str,
            Field(
                description=(
                    "Optional hunger rating or note before eating. "
                    'Examples: "7/10", "very hungry", "not very hungry".'
                )
            ),
        ] = "",
        hunger_after: Annotated[
            str,
            Field(
                description=(
                    "Optional hunger or fullness rating after eating. "
                    'Examples: "full", "8/10", "still hungry".'
                )
            ),
        ] = "",
        notes: Annotated[
            str,
            Field(
                description=(
                    "Optional extra notes about the meal, context, appetite, leftovers, "
                    "or uncertainty in the entry."
                )
            ),
        ] = "",
    ) -> dict:
        """
        Add a meal or eating event to the user's intake history.

        Use this when the user says they ate a meal, snack, drink, takeaway,
        restaurant meal, or homemade meal.

        This creates the parent meal record only. It does not create ingredient
        component rows and does not automatically deduct inventory. Use
        add_intake_item separately to record meal components.
        """
        return add_intake_entry_service(
            date=date,
            time=time,
            meal_type=meal_type,
            meal_name=meal_name,
            meal_description=meal_description,
            source=source,
            amount_eaten=amount_eaten,
            portion_confidence=portion_confidence,
            total_calories_estimate=total_calories_estimate,
            total_protein_g_estimate=total_protein_g_estimate,
            total_carbs_g_estimate=total_carbs_g_estimate,
            total_fat_g_estimate=total_fat_g_estimate,
            total_fibre_g_estimate=total_fibre_g_estimate,
            total_sugar_g_estimate=total_sugar_g_estimate,
            total_sodium_mg_estimate=total_sodium_mg_estimate,
            nutrition_confidence=nutrition_confidence,
            was_finished=was_finished,
            leftovers_created=leftovers_created,
            hunger_before=hunger_before,
            hunger_after=hunger_after,
            notes=notes,
        )

    @mcp.tool()
    def add_intake_item(
        intake_id: str,
        food_item: str,
        brand: str = "",
        category: str = "",
        source: str = "",
        stock_id: str = "",
        amount_eaten: str = "",
        servings_used: float = 0,
        calories_estimate: float = 0,
        protein_g_estimate: float = 0,
        carbs_g_estimate: float = 0,
        fat_g_estimate: float = 0,
        fibre_g_estimate: float = 0,
        sugar_g_estimate: float = 0,
        sodium_mg_estimate: float = 0,
        nutrition_confidence: str = "medium",
        notes: str = "",
    ) -> dict:
        """
        Add a food item, ingredient, or component to an existing intake entry.

        Optional stock_id values are validated by the service layer when supplied.
        This first version does not automatically change inventory.
        """
        return add_intake_item_service(
            intake_id=intake_id,
            food_item=food_item,
            brand=brand,
            category=category,
            source=source,
            stock_id=stock_id,
            amount_eaten=amount_eaten,
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
