from mcp.server.fastmcp import FastMCP

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
        date: str,
        meal_name: str,
        time: str = "",
        meal_type: str = "meal",
        meal_description: str = "",
        source: str = "",
        amount_eaten: str = "",
        portion_confidence: str = "medium",
        total_calories_estimate: float = 0,
        total_protein_g_estimate: float = 0,
        total_carbs_g_estimate: float = 0,
        total_fat_g_estimate: float = 0,
        total_fibre_g_estimate: float = 0,
        total_sugar_g_estimate: float = 0,
        total_sodium_mg_estimate: float = 0,
        nutrition_confidence: str = "medium",
        was_finished: str = "unknown",
        leftovers_created: str = "unknown",
        hunger_before: str = "",
        hunger_after: str = "",
        notes: str = "",
    ) -> dict:
        """
        Add a meal or eating event to the user's intake history.

        This creates the parent intake entry only. It does not automatically
        deduct inventory or create waste records.
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
