from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from grocery_assistant_mcp.utils.paths import (
    INVENTORY_PATH,
    INTAKE_HISTORY_PATH,
    INTAKE_ITEMS_PATH,
)

from grocery_assistant_mcp.core.schemas import (
    INVENTORY_COLUMNS,
    INTAKE_HISTORY_COLUMNS,
    INTAKE_ITEMS_COLUMNS,
)

from grocery_assistant_mcp.core.intake_helpers import (
    clean_and_validate_intake_entry_fields,
    clean_and_validate_intake_item_fields,
)

from grocery_assistant_mcp.core.relationship_helpers import require_existing_id

from grocery_assistant_mcp.core.transaction_helpers import save_related_csv_updates

from grocery_assistant_mcp.core.write_helpers import (
    generate_next_id,
    read_csv_for_write,
)


MEAL_DATA_FIELDS = {
    "date",
    "time",
    "meal_type",
    "meal_name",
    "meal_description",
    "source",
    "amount_eaten",
    "portion_confidence",
    "total_calories_estimate",
    "total_protein_g_estimate",
    "total_carbs_g_estimate",
    "total_fat_g_estimate",
    "total_fibre_g_estimate",
    "total_sugar_g_estimate",
    "total_sodium_mg_estimate",
    "nutrition_confidence",
    "was_finished",
    "leftovers_created",
    "hunger_before",
    "hunger_after",
    "notes",
}


INTAKE_ITEM_DATA_FIELDS = {
    "food_item",
    "brand",
    "category",
    "source",
    "stock_id",
    "amount_eaten",
    "quantity_used",
    "unit",
    "servings_used",
    "calories_estimate",
    "protein_g_estimate",
    "carbs_g_estimate",
    "fat_g_estimate",
    "fibre_g_estimate",
    "sugar_g_estimate",
    "sodium_mg_estimate",
    "nutrition_confidence",
    "notes",
}


def _ensure_mapping(value: object, field_name: str) -> Mapping:
    """
    Validate that a supplied value is dictionary-like.
    """
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a dictionary/object.")

    return value


def _reject_unknown_fields(
    data: Mapping,
    allowed_fields: set[str],
    field_name: str,
) -> None:
    """
    Reject unknown fields instead of silently ignoring them.

    This is useful for agent-facing tools because misspelled field names should
    fail clearly instead of causing data loss.
    """
    unknown_fields = sorted(set(data.keys()) - allowed_fields)

    if unknown_fields:
        joined = ", ".join(unknown_fields)
        raise ValueError(f"{field_name} contains unsupported field(s): {joined}")


def _clean_meal_data(meal_data: Mapping) -> dict:
    """
    Clean and validate parent meal data for a batch meal operation.
    """
    _reject_unknown_fields(meal_data, MEAL_DATA_FIELDS, "meal_data")

    return clean_and_validate_intake_entry_fields(
        date=meal_data.get("date", ""),
        time=meal_data.get("time", ""),
        meal_type=meal_data.get("meal_type", "meal"),
        meal_name=meal_data.get("meal_name", ""),
        meal_description=meal_data.get("meal_description", ""),
        source=meal_data.get("source", ""),
        amount_eaten=meal_data.get("amount_eaten", ""),
        portion_confidence=meal_data.get("portion_confidence", "medium"),
        total_calories_estimate=meal_data.get("total_calories_estimate", 0),
        total_protein_g_estimate=meal_data.get("total_protein_g_estimate", 0),
        total_carbs_g_estimate=meal_data.get("total_carbs_g_estimate", 0),
        total_fat_g_estimate=meal_data.get("total_fat_g_estimate", 0),
        total_fibre_g_estimate=meal_data.get("total_fibre_g_estimate", 0),
        total_sugar_g_estimate=meal_data.get("total_sugar_g_estimate", 0),
        total_sodium_mg_estimate=meal_data.get("total_sodium_mg_estimate", 0),
        nutrition_confidence=meal_data.get("nutrition_confidence", "medium"),
        was_finished=meal_data.get("was_finished", "unknown"),
        leftovers_created=meal_data.get("leftovers_created", "unknown"),
        hunger_before=meal_data.get("hunger_before", ""),
        hunger_after=meal_data.get("hunger_after", ""),
        notes=meal_data.get("notes", ""),
    )


def _clean_intake_item_data(item_data: Mapping, index: int) -> dict:
    """
    Clean and validate one child intake item for a batch meal operation.
    """
    field_name = f"items[{index}]"
    _reject_unknown_fields(item_data, INTAKE_ITEM_DATA_FIELDS, field_name)

    return clean_and_validate_intake_item_fields(
        food_item=item_data.get("food_item", ""),
        brand=item_data.get("brand", ""),
        category=item_data.get("category", ""),
        source=item_data.get("source", ""),
        stock_id=item_data.get("stock_id", ""),
        amount_eaten=item_data.get("amount_eaten", ""),
        quantity_used=item_data.get("quantity_used", 0),
        unit=item_data.get("unit", ""),
        servings_used=item_data.get("servings_used", 0),
        calories_estimate=item_data.get("calories_estimate", 0),
        protein_g_estimate=item_data.get("protein_g_estimate", 0),
        carbs_g_estimate=item_data.get("carbs_g_estimate", 0),
        fat_g_estimate=item_data.get("fat_g_estimate", 0),
        fibre_g_estimate=item_data.get("fibre_g_estimate", 0),
        sugar_g_estimate=item_data.get("sugar_g_estimate", 0),
        sodium_mg_estimate=item_data.get("sodium_mg_estimate", 0),
        nutrition_confidence=item_data.get("nutrition_confidence", "medium"),
        notes=item_data.get("notes", ""),
    )


def _generate_sequential_ids(
    existing_ids: list[str],
    prefix: str,
    count: int,
    width: int = 3,
) -> list[str]:
    """
    Generate multiple sequential IDs without writing after each one.
    """
    generated_ids: list[str] = []
    working_ids = list(existing_ids)

    for _ in range(count):
        next_id = generate_next_id(
            working_ids,
            prefix=prefix,
            width=width,
        )
        generated_ids.append(next_id)
        working_ids.append(next_id)

    return generated_ids


def add_meal_with_items(
    meal_data: dict,
    items: list[dict],
) -> dict:
    """
    Add one parent meal/eating-event and multiple child intake item rows.

    This is the Version 1.4B batch intake workflow.

    It writes to:
    - user_intake_history.csv
    - user_intake_items.csv

    It does not:
    - deduct inventory
    - create inventory consumption records
    - create food waste records
    - auto-calculate parent nutrition totals
    - auto-learn aliases or meal templates

    Optional stock_id values on child items are validated if supplied, but they
    are treated as references only.
    """
    meal_data = _ensure_mapping(meal_data, "meal_data")

    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a list of dictionaries/objects.")

    if len(items) == 0:
        raise ValueError("items must include at least one child intake item.")

    cleaned_meal = _clean_meal_data(meal_data)

    cleaned_items: list[dict] = []

    for index, raw_item in enumerate(items):
        raw_item = _ensure_mapping(raw_item, f"items[{index}]")
        cleaned_items.append(_clean_intake_item_data(raw_item, index))

    history_df = read_csv_for_write(
        INTAKE_HISTORY_PATH,
        INTAKE_HISTORY_COLUMNS,
    )

    intake_items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    )

    stock_ids_to_validate = [
        item["stock_id"]
        for item in cleaned_items
        if item.get("stock_id")
    ]

    if stock_ids_to_validate:
        inventory_df = read_csv_for_write(
            INVENTORY_PATH,
            INVENTORY_COLUMNS,
        )

        for stock_id in stock_ids_to_validate:
            require_existing_id(
                df=inventory_df,
                id_column="stock_id",
                id_value=stock_id,
                entity_name="inventory item",
            )

    existing_intake_ids = history_df["intake_id"].dropna().astype(str).tolist()
    intake_id = generate_next_id(
        existing_intake_ids,
        prefix="intake",
        width=3,
    )

    existing_item_ids = (
        intake_items_df["intake_item_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    intake_item_ids = _generate_sequential_ids(
        existing_ids=existing_item_ids,
        prefix="intake_item",
        count=len(cleaned_items),
        width=3,
    )

    new_entry = {
        "intake_id": intake_id,
        **cleaned_meal,
    }

    new_items = []

    for intake_item_id, item_fields in zip(intake_item_ids, cleaned_items):
        new_items.append({
            "intake_item_id": intake_item_id,
            "intake_id": intake_id,
            **item_fields,
        })

    updated_history_df = pd.concat(
        [history_df, pd.DataFrame([new_entry])],
        ignore_index=True,
    )

    updated_intake_items_df = pd.concat(
        [intake_items_df, pd.DataFrame(new_items)],
        ignore_index=True,
    )

    backup_paths = save_related_csv_updates([
        (
            "intake_history",
            INTAKE_HISTORY_PATH,
            history_df,
            updated_history_df,
        ),
        (
            "intake_items",
            INTAKE_ITEMS_PATH,
            intake_items_df,
            updated_intake_items_df,
        ),
    ])

    return {
        "success": True,
        "message": "Meal and child intake items added.",
        "intake_entry": new_entry,
        "intake_items": new_items,
        "item_count": len(new_items),
        "inventory_deducted": False,
        "consumption_records_created": 0,
        "food_waste_records_created": 0,
        "intake_history_backup_created": backup_paths.get("intake_history"),
        "intake_items_backup_created": backup_paths.get("intake_items"),
    }