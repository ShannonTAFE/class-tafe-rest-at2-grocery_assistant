from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from grocery_assistant_mcp.utils.paths import (
    INVENTORY_CONSUMPTION_PATH,
    INVENTORY_PATH,
    INTAKE_HISTORY_PATH,
    INTAKE_ITEMS_PATH,
)

from grocery_assistant_mcp.core.constants import (
    VALID_CONFIDENCE_LEVELS,
    VALID_CONSUMPTION_TYPES,
    VALID_TRACKING_CONFIDENCE,
)

from grocery_assistant_mcp.core.schemas import (
    INVENTORY_COLUMNS,
    INVENTORY_CONSUMPTION_COLUMNS,
    INTAKE_HISTORY_COLUMNS,
    INTAKE_ITEMS_COLUMNS,
)

from grocery_assistant_mcp.core.consumption_helpers import (
    apply_inventory_consumption_to_df,
    build_intake_item_from_inventory_row,
    build_inventory_consumption_record,
)

from grocery_assistant_mcp.core.intake_helpers import (
    clean_and_validate_intake_entry_fields,
    clean_and_validate_intake_item_fields,
)

from grocery_assistant_mcp.core.transaction_helpers import save_related_csv_updates

from grocery_assistant_mcp.core.write_helpers import (
    clean_text,
    generate_next_id,
    read_csv_for_write,
    validate_choice_or_blank,
    validate_non_negative_fields,
    validate_required_choice,
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


INVENTORY_ITEM_FIELDS = {
    "stock_id",
    "amount_eaten",
    "quantity_used",
    "servings_used",
    "calories_estimate",
    "protein_g_estimate",
    "carbs_g_estimate",
    "fat_g_estimate",
    "fibre_g_estimate",
    "sugar_g_estimate",
    "sodium_mg_estimate",
    "nutrition_confidence",
    "consumption_type",
    "tracking_confidence",
    "notes",
}


MANUAL_ITEM_FIELDS = {
    "food_item",
    "brand",
    "category",
    "source",
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
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a dictionary/object.")

    return value


def _ensure_sequence(value: object, field_name: str) -> Sequence:
    if value is None:
        return []

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a list of dictionaries/objects.")

    return value


def _reject_unknown_fields(
    data: Mapping,
    allowed_fields: set[str],
    field_name: str,
) -> None:
    unknown_fields = sorted(set(data.keys()) - allowed_fields)

    if unknown_fields:
        joined = ", ".join(unknown_fields)
        raise ValueError(f"{field_name} contains unsupported field(s): {joined}")


def _append_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    return pd.concat(
        [df, pd.DataFrame([row])],
        ignore_index=True,
    )


def _clean_meal_data(meal_data: Mapping) -> dict:
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


def _clean_inventory_item_data(
    item_data: Mapping,
    index: int,
    default_consumption_type: str,
    default_tracking_confidence: str,
    default_notes: str,
) -> dict:
    field_name = f"inventory_items[{index}]"
    _reject_unknown_fields(item_data, INVENTORY_ITEM_FIELDS, field_name)

    stock_id = clean_text(
        item_data.get("stock_id", ""),
        "stock_id",
        required=True,
    )

    amount_eaten = clean_text(
        item_data.get("amount_eaten", ""),
        "amount_eaten",
    )

    notes = clean_text(
        item_data.get("notes", default_notes),
        "notes",
    )

    nutrition_confidence = validate_choice_or_blank(
        item_data.get("nutrition_confidence", "medium"),
        VALID_CONFIDENCE_LEVELS,
        "nutrition_confidence",
        default="unknown",
    )

    consumption_type = validate_required_choice(
        item_data.get("consumption_type", default_consumption_type),
        VALID_CONSUMPTION_TYPES,
        "consumption_type",
    )

    tracking_confidence = validate_choice_or_blank(
        item_data.get("tracking_confidence", default_tracking_confidence),
        VALID_TRACKING_CONFIDENCE,
        "tracking_confidence",
        default="medium",
    )

    numeric_values = validate_non_negative_fields({
        "quantity_used": item_data.get("quantity_used", 0),
        "servings_used": item_data.get("servings_used", 0),
        "calories_estimate": item_data.get("calories_estimate", 0),
        "protein_g_estimate": item_data.get("protein_g_estimate", 0),
        "carbs_g_estimate": item_data.get("carbs_g_estimate", 0),
        "fat_g_estimate": item_data.get("fat_g_estimate", 0),
        "fibre_g_estimate": item_data.get("fibre_g_estimate", 0),
        "sugar_g_estimate": item_data.get("sugar_g_estimate", 0),
        "sodium_mg_estimate": item_data.get("sodium_mg_estimate", 0),
    })

    return {
        "stock_id": stock_id,
        "amount_eaten": amount_eaten,
        "quantity_used": numeric_values["quantity_used"],
        "servings_used": numeric_values["servings_used"],
        "calories_estimate": numeric_values["calories_estimate"],
        "protein_g_estimate": numeric_values["protein_g_estimate"],
        "carbs_g_estimate": numeric_values["carbs_g_estimate"],
        "fat_g_estimate": numeric_values["fat_g_estimate"],
        "fibre_g_estimate": numeric_values["fibre_g_estimate"],
        "sugar_g_estimate": numeric_values["sugar_g_estimate"],
        "sodium_mg_estimate": numeric_values["sodium_mg_estimate"],
        "nutrition_confidence": nutrition_confidence,
        "consumption_type": consumption_type,
        "tracking_confidence": tracking_confidence,
        "notes": notes,
    }


def _clean_manual_item_data(item_data: Mapping, index: int) -> dict:
    field_name = f"manual_items[{index}]"

    if "stock_id" in item_data:
        raise ValueError(
            f"{field_name} must not include stock_id. "
            "Use inventory_items for stock-linked ingredients."
        )

    _reject_unknown_fields(item_data, MANUAL_ITEM_FIELDS, field_name)

    return clean_and_validate_intake_item_fields(
        food_item=item_data.get("food_item", ""),
        brand=item_data.get("brand", ""),
        category=item_data.get("category", ""),
        source=item_data.get("source", ""),
        stock_id="",
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


def _reject_duplicate_stock_ids(cleaned_inventory_items: list[dict]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for item in cleaned_inventory_items:
        stock_id = item["stock_id"]

        if stock_id in seen:
            duplicates.add(stock_id)

        seen.add(stock_id)

    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ValueError(
            f"Duplicate stock_id in inventory_items: {joined}. "
            "Combine usage for each stock item into one row."
        )


def _build_manual_intake_item(
    intake_items_df: pd.DataFrame,
    intake_id: str,
    item_data: dict,
) -> dict:
    existing_item_ids = (
        intake_items_df["intake_item_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    intake_item_id = generate_next_id(
        existing_item_ids,
        prefix="intake_item",
        width=3,
    )

    return {
        "intake_item_id": intake_item_id,
        "intake_id": intake_id,
        **item_data,
    }


def _build_inventory_update_summary(
    inventory_before: dict,
    inventory_after: dict,
    quantity_used: float,
    servings_used: float,
) -> dict:
    return {
        "stock_id": inventory_before.get("stock_id", ""),
        "food_item": inventory_before.get("food_item", ""),
        "quantity_before": inventory_before.get("quantity", 0),
        "quantity_used": quantity_used,
        "quantity_after": inventory_after.get("quantity", 0),
        "servings_before": inventory_before.get("servings_remaining", 0),
        "servings_used": servings_used,
        "servings_after": inventory_after.get("servings_remaining", 0),
        "stock_status_before": inventory_before.get("stock_status", ""),
        "stock_status_after": inventory_after.get("stock_status", ""),
    }


def add_meal_with_inventory_items(
    meal_data: dict,
    inventory_items: list[dict],
    manual_items: list[dict] | None = None,
    consumption_type: str = "consumed",
    tracking_confidence: str = "medium",
    notes: str = "",
) -> dict:
    """
    Add one parent meal, child intake items, selected inventory deductions,
    and linked inventory consumption records.

    This is the Version 1.4C inventory-linked batch meal workflow.

    It writes to:
    - user_intake_history.csv
    - user_intake_items.csv
    - user_inventory.csv
    - user_inventory_consumption.csv

    It does not:
    - create food waste records
    - auto-learn meal aliases
    - auto-create meal templates
    - auto-calculate parent nutrition totals
    - perform unit conversion
    """
    meal_data = _ensure_mapping(meal_data, "meal_data")
    inventory_items = _ensure_sequence(inventory_items, "inventory_items")
    manual_items = _ensure_sequence(manual_items, "manual_items")

    if len(inventory_items) == 0:
        raise ValueError("inventory_items must include at least one inventory-linked item.")

    default_consumption_type = validate_required_choice(
        consumption_type,
        VALID_CONSUMPTION_TYPES,
        "consumption_type",
    )

    default_tracking_confidence = validate_choice_or_blank(
        tracking_confidence,
        VALID_TRACKING_CONFIDENCE,
        "tracking_confidence",
        default="medium",
    )

    default_notes = clean_text(notes, "notes")

    cleaned_meal = _clean_meal_data(meal_data)

    cleaned_inventory_items = [
        _clean_inventory_item_data(
            item_data=_ensure_mapping(raw_item, f"inventory_items[{index}]"),
            index=index,
            default_consumption_type=default_consumption_type,
            default_tracking_confidence=default_tracking_confidence,
            default_notes=default_notes,
        )
        for index, raw_item in enumerate(inventory_items)
    ]

    cleaned_manual_items = [
        _clean_manual_item_data(
            item_data=_ensure_mapping(raw_item, f"manual_items[{index}]"),
            index=index,
        )
        for index, raw_item in enumerate(manual_items)
    ]

    _reject_duplicate_stock_ids(cleaned_inventory_items)

    history_df = read_csv_for_write(
        INTAKE_HISTORY_PATH,
        INTAKE_HISTORY_COLUMNS,
    )

    intake_items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    )

    inventory_df = read_csv_for_write(
        INVENTORY_PATH,
        INVENTORY_COLUMNS,
    )

    consumption_df = read_csv_for_write(
        INVENTORY_CONSUMPTION_PATH,
        INVENTORY_CONSUMPTION_COLUMNS,
    )

    existing_intake_ids = (
        history_df["intake_id"]
        .dropna()
        .astype(str)
        .tolist()
    )

    intake_id = generate_next_id(
        existing_intake_ids,
        prefix="intake",
        width=3,
    )

    new_entry = {
        "intake_id": intake_id,
        **cleaned_meal,
    }

    working_history_df = _append_row(history_df, new_entry)
    working_intake_items_df = intake_items_df.copy()
    working_inventory_df = inventory_df.copy()
    working_consumption_df = consumption_df.copy()

    new_items: list[dict] = []
    new_consumption_records: list[dict] = []
    inventory_updates: list[dict] = []

    for item in cleaned_inventory_items:
        (
            working_inventory_df,
            inventory_before,
            inventory_after,
            consumption_values,
        ) = apply_inventory_consumption_to_df(
            inventory_df=working_inventory_df,
            stock_id=item["stock_id"],
            quantity_used=item["quantity_used"],
            servings_used=item["servings_used"],
        )

        quantity_used = consumption_values["quantity_used"]
        servings_used = consumption_values["servings_used"]

        new_intake_item = build_intake_item_from_inventory_row(
            intake_items_df=working_intake_items_df,
            intake_id=intake_id,
            inventory_item=inventory_before,
            amount_eaten=item["amount_eaten"],
            quantity_used=quantity_used,
            servings_used=servings_used,
            calories_estimate=item["calories_estimate"],
            protein_g_estimate=item["protein_g_estimate"],
            carbs_g_estimate=item["carbs_g_estimate"],
            fat_g_estimate=item["fat_g_estimate"],
            fibre_g_estimate=item["fibre_g_estimate"],
            sugar_g_estimate=item["sugar_g_estimate"],
            sodium_mg_estimate=item["sodium_mg_estimate"],
            nutrition_confidence=item["nutrition_confidence"],
            notes=item["notes"],
        )

        working_intake_items_df = _append_row(
            working_intake_items_df,
            new_intake_item,
        )

        consumption_record = build_inventory_consumption_record(
            consumption_df=working_consumption_df,
            inventory_before=inventory_before,
            inventory_after=inventory_after,
            quantity_used=quantity_used,
            servings_used=servings_used,
            intake_id=intake_id,
            intake_item_id=new_intake_item["intake_item_id"],
            consumption_type=item["consumption_type"],
            tracking_confidence=item["tracking_confidence"],
            notes=item["notes"],
        )

        working_consumption_df = _append_row(
            working_consumption_df,
            consumption_record,
        )

        new_items.append(new_intake_item)
        new_consumption_records.append(consumption_record)
        inventory_updates.append(
            _build_inventory_update_summary(
                inventory_before=inventory_before,
                inventory_after=inventory_after,
                quantity_used=quantity_used,
                servings_used=servings_used,
            )
        )

    for item in cleaned_manual_items:
        new_manual_item = _build_manual_intake_item(
            intake_items_df=working_intake_items_df,
            intake_id=intake_id,
            item_data=item,
        )

        working_intake_items_df = _append_row(
            working_intake_items_df,
            new_manual_item,
        )

        new_items.append(new_manual_item)

    backup_paths = save_related_csv_updates([
        (
            "intake_history",
            INTAKE_HISTORY_PATH,
            history_df,
            working_history_df,
        ),
        (
            "intake_items",
            INTAKE_ITEMS_PATH,
            intake_items_df,
            working_intake_items_df,
        ),
        (
            "inventory",
            INVENTORY_PATH,
            inventory_df,
            working_inventory_df,
        ),
        (
            "inventory_consumption",
            INVENTORY_CONSUMPTION_PATH,
            consumption_df,
            working_consumption_df,
        ),
    ])

    return {
        "success": True,
        "message": "Inventory-linked meal and child intake items added.",
        "intake_entry": new_entry,
        "intake_items": new_items,
        "consumption_records": new_consumption_records,
        "inventory_updates": inventory_updates,
        "item_count": len(new_items),
        "inventory_item_count": len(cleaned_inventory_items),
        "manual_item_count": len(cleaned_manual_items),
        "inventory_deducted": True,
        "consumption_records_created": len(new_consumption_records),
        "food_waste_records_created": 0,
        "backup_paths": {
            "intake_history": backup_paths.get("intake_history"),
            "intake_items": backup_paths.get("intake_items"),
            "inventory": backup_paths.get("inventory"),
            "inventory_consumption": backup_paths.get("inventory_consumption"),
        },
    }