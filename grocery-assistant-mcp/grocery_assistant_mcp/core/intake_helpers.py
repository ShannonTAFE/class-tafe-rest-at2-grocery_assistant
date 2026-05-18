from __future__ import annotations

from grocery_assistant_mcp.core.constants import (
    VALID_CONFIDENCE_LEVELS,
    VALID_FINISHED_STATUSES,
    VALID_MEAL_TYPES,
    VALID_YES_NO_UNKNOWN,
)
from grocery_assistant_mcp.core.write_helpers import (
    clean_text,
    validate_choice_or_blank,
    validate_date_or_blank,
    validate_non_negative_fields,
    validate_non_negative_number,
    validate_required_choice,
    validate_required_date,
    validate_time_or_blank,
)


INTAKE_ENTRY_NUMERIC_FIELDS = [
    "total_calories_estimate",
    "total_protein_g_estimate",
    "total_carbs_g_estimate",
    "total_fat_g_estimate",
    "total_fibre_g_estimate",
    "total_sugar_g_estimate",
    "total_sodium_mg_estimate",
]


INTAKE_ITEM_NUMERIC_FIELDS = [
    "quantity_used",
    "servings_used",
    "calories_estimate",
    "protein_g_estimate",
    "carbs_g_estimate",
    "fat_g_estimate",
    "fibre_g_estimate",
    "sugar_g_estimate",
    "sodium_mg_estimate",
]


def clean_and_validate_intake_entry_fields(
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
    Clean and validate fields for a parent intake entry.

    This function performs no file reads or writes.
    """
    cleaned_date = clean_text(date, "date", required=True)
    cleaned_meal_name = clean_text(meal_name, "meal_name", required=True)
    cleaned_time = clean_text(time, "time")
    cleaned_meal_description = clean_text(meal_description)
    cleaned_source = clean_text(source)
    cleaned_amount_eaten = clean_text(amount_eaten)
    cleaned_hunger_before = clean_text(hunger_before)
    cleaned_hunger_after = clean_text(hunger_after)
    cleaned_notes = clean_text(notes)

    validate_date_or_blank(cleaned_date, "date")
    validate_time_or_blank(cleaned_time, "time")

    cleaned_meal_type = validate_required_choice(
        meal_type,
        VALID_MEAL_TYPES,
        "meal_type",
    )

    cleaned_portion_confidence = validate_choice_or_blank(
        portion_confidence,
        VALID_CONFIDENCE_LEVELS,
        "portion_confidence",
        default="unknown",
    )

    cleaned_nutrition_confidence = validate_choice_or_blank(
        nutrition_confidence,
        VALID_CONFIDENCE_LEVELS,
        "nutrition_confidence",
        default="unknown",
    )

    cleaned_was_finished = validate_choice_or_blank(
        was_finished,
        VALID_FINISHED_STATUSES,
        "was_finished",
        default="unknown",
    )

    cleaned_leftovers_created = validate_choice_or_blank(
        leftovers_created,
        VALID_YES_NO_UNKNOWN,
        "leftovers_created",
        default="unknown",
    )

    numeric_values = validate_non_negative_fields({
        "total_calories_estimate": total_calories_estimate,
        "total_protein_g_estimate": total_protein_g_estimate,
        "total_carbs_g_estimate": total_carbs_g_estimate,
        "total_fat_g_estimate": total_fat_g_estimate,
        "total_fibre_g_estimate": total_fibre_g_estimate,
        "total_sugar_g_estimate": total_sugar_g_estimate,
        "total_sodium_mg_estimate": total_sodium_mg_estimate,
    })

    return {
        "date": cleaned_date,
        "time": cleaned_time,
        "meal_type": cleaned_meal_type,
        "meal_name": cleaned_meal_name,
        "meal_description": cleaned_meal_description,
        "source": cleaned_source,
        "amount_eaten": cleaned_amount_eaten,
        "portion_confidence": cleaned_portion_confidence,
        "total_calories_estimate": numeric_values["total_calories_estimate"],
        "total_protein_g_estimate": numeric_values["total_protein_g_estimate"],
        "total_carbs_g_estimate": numeric_values["total_carbs_g_estimate"],
        "total_fat_g_estimate": numeric_values["total_fat_g_estimate"],
        "total_fibre_g_estimate": numeric_values["total_fibre_g_estimate"],
        "total_sugar_g_estimate": numeric_values["total_sugar_g_estimate"],
        "total_sodium_mg_estimate": numeric_values["total_sodium_mg_estimate"],
        "nutrition_confidence": cleaned_nutrition_confidence,
        "was_finished": cleaned_was_finished,
        "leftovers_created": cleaned_leftovers_created,
        "hunger_before": cleaned_hunger_before,
        "hunger_after": cleaned_hunger_after,
        "notes": cleaned_notes,
    }


def clean_and_validate_intake_item_fields(
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
    Clean and validate fields for a child intake item.

    This function performs no file reads or writes.
    It does not validate whether stock_id exists; callers decide that.
    """
    cleaned_food_item = clean_text(food_item, "food_item", required=True)
    cleaned_brand = clean_text(brand, "brand")
    cleaned_category = clean_text(category, "category")
    cleaned_source = clean_text(source, "source")
    cleaned_stock_id = clean_text(stock_id, "stock_id")
    cleaned_amount_eaten = clean_text(amount_eaten, "amount_eaten")
    cleaned_unit = clean_text(unit, "unit")
    cleaned_notes = clean_text(notes, "notes")

    cleaned_nutrition_confidence = validate_choice_or_blank(
        nutrition_confidence,
        VALID_CONFIDENCE_LEVELS,
        "nutrition_confidence",
        default="unknown",
    )

    numeric_values = validate_non_negative_fields({
        "quantity_used": quantity_used,
        "servings_used": servings_used,
        "calories_estimate": calories_estimate,
        "protein_g_estimate": protein_g_estimate,
        "carbs_g_estimate": carbs_g_estimate,
        "fat_g_estimate": fat_g_estimate,
        "fibre_g_estimate": fibre_g_estimate,
        "sugar_g_estimate": sugar_g_estimate,
        "sodium_mg_estimate": sodium_mg_estimate,
    })

    return {
        "food_item": cleaned_food_item,
        "brand": cleaned_brand,
        "category": cleaned_category,
        "source": cleaned_source,
        "stock_id": cleaned_stock_id,
        "amount_eaten": cleaned_amount_eaten,
        "quantity_used": numeric_values["quantity_used"],
        "unit": cleaned_unit,
        "servings_used": numeric_values["servings_used"],
        "calories_estimate": numeric_values["calories_estimate"],
        "protein_g_estimate": numeric_values["protein_g_estimate"],
        "carbs_g_estimate": numeric_values["carbs_g_estimate"],
        "fat_g_estimate": numeric_values["fat_g_estimate"],
        "fibre_g_estimate": numeric_values["fibre_g_estimate"],
        "sugar_g_estimate": numeric_values["sugar_g_estimate"],
        "sodium_mg_estimate": numeric_values["sodium_mg_estimate"],
        "nutrition_confidence": cleaned_nutrition_confidence,
        "notes": cleaned_notes,
    }


def validate_intake_entry_updates(updates: dict) -> dict:
    """
    Clean and validate update fields for a parent intake entry.

    Fields omitted from updates are not changed.
    """
    cleaned_updates = dict(updates)

    text_fields = [
        "date",
        "time",
        "meal_name",
        "meal_description",
        "source",
        "amount_eaten",
        "hunger_before",
        "hunger_after",
        "notes",
    ]

    for field in text_fields:
        if field in cleaned_updates:
            cleaned_updates[field] = clean_text(
                cleaned_updates[field],
                field,
                required=(field in {"date", "meal_name"}),
            )

    if "date" in cleaned_updates:
        validate_required_date(cleaned_updates["date"], "date")

    if "time" in cleaned_updates:
        validate_time_or_blank(cleaned_updates["time"], "time")

    if "meal_type" in cleaned_updates:
        cleaned_updates["meal_type"] = validate_required_choice(
            cleaned_updates["meal_type"],
            VALID_MEAL_TYPES,
            "meal_type",
        )

    if "portion_confidence" in cleaned_updates:
        cleaned_updates["portion_confidence"] = validate_choice_or_blank(
            cleaned_updates["portion_confidence"],
            VALID_CONFIDENCE_LEVELS,
            "portion_confidence",
            default="unknown",
        )

    if "nutrition_confidence" in cleaned_updates:
        cleaned_updates["nutrition_confidence"] = validate_choice_or_blank(
            cleaned_updates["nutrition_confidence"],
            VALID_CONFIDENCE_LEVELS,
            "nutrition_confidence",
            default="unknown",
        )

    if "was_finished" in cleaned_updates:
        cleaned_updates["was_finished"] = validate_choice_or_blank(
            cleaned_updates["was_finished"],
            VALID_FINISHED_STATUSES,
            "was_finished",
            default="unknown",
        )

    if "leftovers_created" in cleaned_updates:
        cleaned_updates["leftovers_created"] = validate_choice_or_blank(
            cleaned_updates["leftovers_created"],
            VALID_YES_NO_UNKNOWN,
            "leftovers_created",
            default="unknown",
        )

    for field in INTAKE_ENTRY_NUMERIC_FIELDS:
        if field in cleaned_updates:
            cleaned_updates[field] = validate_non_negative_number(
                cleaned_updates[field],
                field,
            )

    return cleaned_updates


def validate_intake_item_updates(updates: dict) -> dict:
    """
    Clean and validate update fields for a child intake item.

    Relationship validation for intake_id and stock_id remains with the caller.
    """
    cleaned_updates = dict(updates)

    text_fields = [
        "intake_id",
        "food_item",
        "brand",
        "category",
        "source",
        "stock_id",
        "amount_eaten",
        "unit",
        "notes",
    ]

    for field in text_fields:
        if field in cleaned_updates:
            cleaned_updates[field] = clean_text(
                cleaned_updates[field],
                field,
                required=(field in {"intake_id", "food_item"}),
            )

    if "nutrition_confidence" in cleaned_updates:
        cleaned_updates["nutrition_confidence"] = validate_choice_or_blank(
            cleaned_updates["nutrition_confidence"],
            VALID_CONFIDENCE_LEVELS,
            "nutrition_confidence",
            default="unknown",
        )

    for field in INTAKE_ITEM_NUMERIC_FIELDS:
        if field in cleaned_updates:
            cleaned_updates[field] = validate_non_negative_number(
                cleaned_updates[field],
                field,
            )

    return cleaned_updates