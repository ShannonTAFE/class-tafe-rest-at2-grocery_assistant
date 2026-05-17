from typing import Annotated, Optional

import mcp
from pydantic import Field
from mcp.server.fastmcp import FastMCP

from grocery_assistant_mcp.core.grocery_service import (
    add_intake_entry as add_intake_entry_service,
    add_intake_item as add_intake_item_service,
    get_daily_intake_summary as get_daily_intake_summary_service,
    get_recent_intake as get_recent_intake_service,
    remove_intake_entry as remove_intake_entry_service,
    remove_intake_item as remove_intake_item_service,
    search_intake as search_intake_service,
    update_intake_entry as update_intake_entry_service,
    update_intake_item as update_intake_item_service,
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
        quantity_used: float = 0,
        unit: str = "",
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
            quantity_used=quantity_used,
            unit=unit,
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

    @mcp.tool()
    def update_intake_entry(
        intake_id: Annotated[
            str,
            Field(description='Existing parent intake ID to update. Example: "intake_001".'),
        ],
        date: Optional[str] = None,
        time: Optional[str] = None,
        meal_type: Optional[str] = None,
        meal_name: Optional[str] = None,
        meal_description: Optional[str] = None,
        source: Optional[str] = None,
        amount_eaten: Optional[str] = None,
        portion_confidence: Optional[str] = None,
        total_calories_estimate: Optional[float] = None,
        total_protein_g_estimate: Optional[float] = None,
        total_carbs_g_estimate: Optional[float] = None,
        total_fat_g_estimate: Optional[float] = None,
        total_fibre_g_estimate: Optional[float] = None,
        total_sugar_g_estimate: Optional[float] = None,
        total_sodium_mg_estimate: Optional[float] = None,
        nutrition_confidence: Optional[str] = None,
        was_finished: Optional[str] = None,
        leftovers_created: Optional[str] = None,
        hunger_before: Optional[str] = None,
        hunger_after: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Update an existing parent meal or eating event.

        Only supplied fields are changed. This does not automatically update
        child intake items or inventory.
        """
        return update_intake_entry_service(
            intake_id=intake_id,
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
    def update_intake_item(
        intake_item_id: Annotated[
            str,
            Field(description='Existing child intake item ID to update. Example: "intake_item_001".'),
        ],
        intake_id: Optional[str] = None,
        food_item: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        stock_id: Optional[str] = None,
        amount_eaten: Optional[str] = None,
        quantity_used: Optional[float] = None,
        unit: Optional[str] = None,
        servings_used: Optional[float] = None,
        calories_estimate: Optional[float] = None,
        protein_g_estimate: Optional[float] = None,
        carbs_g_estimate: Optional[float] = None,
        fat_g_estimate: Optional[float] = None,
        fibre_g_estimate: Optional[float] = None,
        sugar_g_estimate: Optional[float] = None,
        sodium_mg_estimate: Optional[float] = None,
        nutrition_confidence: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Update an existing ingredient, food item, or component attached to an
        intake entry.

        If intake_id is changed, the new parent intake entry must exist.
        If stock_id is supplied and not blank, the inventory item must exist.
        """
        return update_intake_item_service(
            intake_item_id=intake_item_id,
            intake_id=intake_id,
            food_item=food_item,
            brand=brand,
            category=category,
            source=source,
            stock_id=stock_id,
            amount_eaten=amount_eaten,
            quantity_used=quantity_used,
            unit=unit,
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

    @mcp.tool()
    def remove_intake_entry(
        intake_id: Annotated[
            str,
            Field(description='Existing parent intake ID to remove. Example: "intake_001".'),
        ],
    ) -> dict:
        """
        Remove a parent meal entry only when it has no child intake items.

        If child intake items exist, remove them first with remove_intake_item.
        This avoids orphaned records.
        """
        return remove_intake_entry_service(intake_id=intake_id)

    @mcp.tool()
    def remove_intake_item(
        intake_item_id: Annotated[
            str,
            Field(description='Existing child intake item ID to remove. Example: "intake_item_001".'),
        ],
    ) -> dict:
        """
        Remove one child intake item.

        This does not remove the parent meal entry.
        """
        return remove_intake_item_service(intake_item_id=intake_item_id)

    @mcp.tool()
    def search_intake(
        query: Annotated[
            str,
            Field(
                description=(
                    "Optional text search across parent meal entries and child intake items. "
                    'Use this for searches like "spaghetti", "chicken", "takeaway", '
                    '"leftovers", or "large bowl". Leave blank when filtering only by ID, '
                    "date, meal type, source, stock ID, or category."
                )
            ),
        ] = "",
        intake_id: Annotated[
            str,
            Field(
                description=(
                    "Optional parent intake entry ID to inspect. "
                    'Example: "intake_001". When supplied, the matching parent entry '
                    "and its child items are returned."
                )
            ),
        ] = "",
        intake_item_id: Annotated[
            str,
            Field(
                description=(
                    "Optional child intake item ID to inspect. "
                    'Example: "intake_item_001". When supplied, the matching child item '
                    "is returned with parent meal context."
                )
            ),
        ] = "",
        date: Annotated[
            str,
            Field(
                description=(
                    "Optional exact intake date filter in YYYY-MM-DD format. "
                    'Example: "2026-05-17".'
                )
            ),
        ] = "",
        date_from: Annotated[
            str,
            Field(
                description=(
                    "Optional start date for a date range filter in YYYY-MM-DD format. "
                    'Example: "2026-05-01".'
                )
            ),
        ] = "",
        date_to: Annotated[
            str,
            Field(
                description=(
                    "Optional end date for a date range filter in YYYY-MM-DD format. "
                    'Example: "2026-05-17".'
                )
            ),
        ] = "",
        meal_type: Annotated[
            str,
            Field(
                description=(
                    "Optional meal type filter. Use values such as breakfast, lunch, "
                    "dinner, snack, or drink depending on the allowed project values."
                )
            ),
        ] = "",
        source: Annotated[
            str,
            Field(
                description=(
                    "Optional source filter. Searches parent entry source and child item "
                    'source. Examples: "home", "takeaway", "restaurant", "inventory".'
                )
            ),
        ] = "",
        stock_id: Annotated[
            str,
            Field(
                description=(
                    "Optional inventory stock ID filter for child intake items. "
                    'Example: "inv_001". Useful for finding where an inventory item '
                    "was used in intake records."
                )
            ),
        ] = "",
        category: Annotated[
            str,
            Field(
                description=(
                    "Optional child item category filter. Examples: protein, pantry, "
                    "dairy, vegetable, fruit, snack."
                )
            ),
        ] = "",
        limit: Annotated[
            int,
            Field(
                description=(
                    "Maximum number of matching parent entries and matching child items "
                    "to return. Defaults to 20 and is capped by the service layer."
                )
            ),
        ] = 20,
    ) -> dict:
        """
        Search intake parent entries and child item records.

        This is a read-only Version 1.2 workflow tool. It helps locate
        intake_id and intake_item_id values before calling update or remove
        tools. It also returns relationship context so parent entries are not
        removed while child items still exist.
        """
        return search_intake_service(
            query=query,
            intake_id=intake_id,
            intake_item_id=intake_item_id,
            date=date,
            date_from=date_from,
            date_to=date_to,
            meal_type=meal_type,
            source=source,
            stock_id=stock_id,
            category=category,
            limit=limit,
        )