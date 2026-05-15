from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from grocery_assistant_mcp.utils.paths import (
    INVENTORY_PATH,
    INTAKE_HISTORY_PATH,
    INTAKE_ITEMS_PATH,
    FOOD_WASTE_PATH,
)

from grocery_assistant_mcp.core.write_helpers import (
    backup_csv,
    generate_next_id,
    read_csv_for_write,
    require_non_empty,
    save_csv,
    validate_date_or_blank,
    validate_non_negative_number,
)

logger = logging.getLogger("grocery_mcp.grocery_data")


# ---------------------------------------------------------------------
# CSV schemas
# ---------------------------------------------------------------------

INVENTORY_COLUMNS = [
    "stock_id",
    "food_item",
    "brand",
    "category",
    "location",
    "quantity",
    "unit",
    "servings_remaining",
    "initial_quantity",
    "initial_servings",
    "stock_status",
    "expiry_date",
    "date_added",
    "notes",
]

FOOD_WASTE_COLUMNS = [
    "waste_id",
    "stock_id",
    "food_item",
    "brand",
    "category",
    "location",
    "initial_quantity",
    "initial_unit",
    "initial_servings",
    "quantity_wasted",
    "unit",
    "servings_wasted",
    "estimated_quantity_consumed",
    "estimated_servings_consumed",
    "date_added",
    "expiry_date",
    "wasted_at",
    "waste_type",
    "waste_reason",
    "tracking_confidence",
    "notes",
]


# ---------------------------------------------------------------------
# Valid values
# ---------------------------------------------------------------------

VALID_STOCK_STATUSES = {
    "ok",
    "low",
    "very low",
    "empty",
    "out",
    "used",
    "expired",
    "removed",
}

VALID_REMOVAL_TYPES = {
    "used_up",
    "expired",
    "spoiled",
    "discarded",
    "unused",
    "overbought",
    "did_not_like",
    "duplicate_entry",
    "incorrect_entry",
    "test_entry",
    "unknown",
}

WASTE_REMOVAL_TYPES = {
    "expired",
    "spoiled",
    "discarded",
    "unused",
    "overbought",
    "did_not_like",
}

VALID_TRACKING_CONFIDENCE = {
    "low",
    "medium",
    "high",
}


# ---------------------------------------------------------------------
# Small service helpers
# ---------------------------------------------------------------------

def today_iso() -> str:
    """Return today's date in YYYY-MM-DD format."""
    return date.today().isoformat()


def to_float(value: object, default: float = 0.0) -> float:
    """
    Convert a CSV value to float.

    Blank, missing, or invalid values return the supplied default.
    """
    if value is None:
        return default

    if str(value).strip() == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_choice(value: object, valid_values: set[str], field_name: str) -> str:
    """
    Normalize and validate a string choice.

    Returns the cleaned lowercase value.
    """
    cleaned = str(value or "").strip().lower()

    if cleaned not in valid_values:
        allowed = ", ".join(sorted(valid_values))
        raise ValueError(f"{field_name} must be one of: {allowed}")

    return cleaned


# ---------------------------------------------------------------------
# Read helpers and read-only service functions
# ---------------------------------------------------------------------


def read_csv_file(path: Path) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame.

    If the file does not exist, return an empty DataFrame
    instead of crashing the MCP server.
    """
    if not path.exists():
        logger.warning("CSV file not found: %s", path)
        return pd.DataFrame()

    return pd.read_csv(path)


def read_inventory() -> pd.DataFrame:
    """
    Read the active inventory CSV.

    This backs the grocery://inventory MCP resource.
    """
    return read_csv_file(INVENTORY_PATH)


def read_food_waste() -> pd.DataFrame:
    """
    Read the food waste CSV.

    This can back a future grocery://food-waste MCP resource.
    """
    return read_csv_file(FOOD_WASTE_PATH)


def read_intake_history() -> pd.DataFrame:
    """
    Read the intake history CSV.

    This backs the grocery://intake-history MCP resource.
    """
    return read_csv_file(INTAKE_HISTORY_PATH)


def read_intake_items() -> pd.DataFrame:
    """
    Read the intake items CSV.

    This backs the grocery://intake-items MCP resource.
    """
    return read_csv_file(INTAKE_ITEMS_PATH)


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """
    Convert a pandas DataFrame into a list of dictionaries.

    This format is easy for MCP tools to return.
    """
    if df.empty:
        return []

    return df.fillna("").to_dict(orient="records")


def to_json(data) -> str:
    """
    Convert Python data into formatted JSON text.

    This is useful for MCP resources.
    """
    return json.dumps(data, indent=2, ensure_ascii=False)


def _safe_text_series(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Convert a text column into lowercase strings safely.

    This avoids errors if some values are blank or missing.
    """
    return df[column].fillna("").astype(str).str.lower()


def list_inventory_items(
    category: str | None = None,
    low_stock_only: bool = False,
) -> list[dict]:
    """
    Return active inventory items.

    Optional filters:
    - category
    - low_stock_only
    """
    df = read_inventory()

    if df.empty:
        return []

    if category and "category" in df.columns:
        df = df[_safe_text_series(df, "category") == category.lower()]

    if low_stock_only and "stock_status" in df.columns:
        low_statuses = ["low", "very low", "empty", "out"]
        df = df[_safe_text_series(df, "stock_status").isin(low_statuses)]

    return df_to_records(df)


def list_food_waste_items(
    waste_type: str = "",
    category: str = "",
) -> list[dict]:
    """
    Return food waste records.

    Optional filters:
    - waste_type
    - category

    This is useful for a future MCP resource or read-only tool.
    """
    df = read_food_waste()

    if df.empty:
        return []

    waste_type = waste_type.strip().lower()
    category = category.strip().lower()

    if waste_type and "waste_type" in df.columns:
        df = df[_safe_text_series(df, "waste_type") == waste_type]

    if category and "category" in df.columns:
        df = df[_safe_text_series(df, "category") == category]

    return df_to_records(df)


def find_inventory_item(search_term: str) -> list[dict]:
    """
    Search the active inventory for an item.

    Searches:
    - food_item
    - brand
    - category
    - location
    - notes
    """
    df = read_inventory()

    if df.empty:
        return []

    term = search_term.lower()
    searchable_columns = ["food_item", "brand", "category", "location", "notes"]

    mask = pd.Series(False, index=df.index)

    for column in searchable_columns:
        if column in df.columns:
            mask = mask | _safe_text_series(df, column).str.contains(
                term,
                regex=False,
            )

    results = df[mask]

    return df_to_records(results)


def get_daily_intake_summary(date: str) -> dict:
    """
    Return all logged meals and food items for a selected date,
    with calculated nutrition totals.

    Hybrid nutrition strategy:
    - If a meal has item-level breakdown rows, use those item totals.
    - If a meal has no item-level rows, fall back to the meal-level total_* columns.

    This supports both:
    - detailed ingredient breakdown logs
    - quick/manual meal logs
    """
    history_df = read_intake_history()
    items_df = read_intake_items()

    # 1. Filter meal-level history rows by date.
    if history_df.empty or "date" not in history_df.columns:
        day_history = pd.DataFrame()
    else:
        day_history = history_df[history_df["date"].astype(str) == date].copy()

    # 2. Collect intake IDs for the selected date.
    if not day_history.empty and "intake_id" in day_history.columns:
        intake_ids = (
            day_history["intake_id"]
            .fillna("")
            .astype(str)
            .str.strip()
            .tolist()
        )
        intake_ids = [intake_id for intake_id in intake_ids if intake_id]
    else:
        intake_ids = []

    # 3. Get matching item-level rows using intake_id.
    if items_df.empty:
        day_items = pd.DataFrame()
    elif "intake_id" in items_df.columns and intake_ids:
        day_items = items_df[
            items_df["intake_id"]
            .fillna("")
            .astype(str)
            .str.strip()
            .isin(intake_ids)
        ].copy()
    elif "date" in items_df.columns:
        day_items = items_df[items_df["date"].astype(str) == date].copy()
    else:
        day_items = pd.DataFrame()

    # 4. Define nutrition column mapping.
    # Output names are consistent regardless of source.
    item_nutrition_columns = {
        "calories_estimate": "calories_estimate",
        "protein_g_estimate": "protein_g_estimate",
        "carbs_g_estimate": "carbs_g_estimate",
        "fat_g_estimate": "fat_g_estimate",
        "fibre_g_estimate": "fibre_g_estimate",
        "sugar_g_estimate": "sugar_g_estimate",
        "sodium_mg_estimate": "sodium_mg_estimate",
    }

    meal_nutrition_columns = {
        "calories_estimate": "total_calories_estimate",
        "protein_g_estimate": "total_protein_g_estimate",
        "carbs_g_estimate": "total_carbs_g_estimate",
        "fat_g_estimate": "total_fat_g_estimate",
        "fibre_g_estimate": "total_fibre_g_estimate",
        "sugar_g_estimate": "total_sugar_g_estimate",
        "sodium_mg_estimate": "total_sodium_mg_estimate",
    }

    # 5. Prepare totals.
    nutrition_totals = {
        output_name: 0.0
        for output_name in item_nutrition_columns.keys()
    }

    missing_nutrition_counts = {
        output_name: 0
        for output_name in item_nutrition_columns.keys()
    }

    meal_ids_using_item_totals = []
    meal_ids_using_meal_totals = []

    # 6. Group items by intake_id for quick lookup.
    if not day_items.empty and "intake_id" in day_items.columns:
        item_groups = {
            str(intake_id).strip(): group.copy()
            for intake_id, group in day_items.groupby(
                day_items["intake_id"].fillna("").astype(str).str.strip()
            )
        }
    else:
        item_groups = {}

    # 7. Calculate hybrid totals meal by meal.
    for _, meal_row in day_history.iterrows():
        intake_id = str(meal_row.get("intake_id", "")).strip()

        item_group = item_groups.get(intake_id)

        if item_group is not None and not item_group.empty:
            # Use item-level totals for this meal.
            meal_ids_using_item_totals.append(intake_id)

            for output_name, source_column in item_nutrition_columns.items():
                if source_column in item_group.columns:
                    numeric_values = pd.to_numeric(
                        item_group[source_column],
                        errors="coerce",
                    )

                    nutrition_totals[output_name] += float(
                        numeric_values.fillna(0).sum()
                    )

                    missing_nutrition_counts[output_name] += int(
                        numeric_values.isna().sum()
                    )
                else:
                    missing_nutrition_counts[output_name] += int(len(item_group))

        else:
            # Fall back to meal-level total_* columns.
            meal_ids_using_meal_totals.append(intake_id)

            for output_name, source_column in meal_nutrition_columns.items():
                if source_column in day_history.columns:
                    value = pd.to_numeric(
                        pd.Series([meal_row.get(source_column)]),
                        errors="coerce",
                    ).iloc[0]

                    if pd.isna(value):
                        missing_nutrition_counts[output_name] += 1
                    else:
                        nutrition_totals[output_name] += float(value)
                else:
                    missing_nutrition_counts[output_name] += 1

    return {
        "date": date,
        "meal_count": int(len(day_history)),
        "item_count": int(len(day_items)),
        "nutrition_totals_source": "hybrid_items_with_meal_fallback",
        "meal_ids_using_item_totals": meal_ids_using_item_totals,
        "meal_ids_using_meal_totals": meal_ids_using_meal_totals,
        "meals": df_to_records(day_history),
        "items": df_to_records(day_items),
        "nutrition_totals": nutrition_totals,
        "missing_nutrition_counts": missing_nutrition_counts,
    }


def search_inventory(
    query: str = "",
    category: str = "",
    location: str = "",
) -> list[dict]:
    """
    Search the active inventory by query, category, and location.

    Query searches across:
    - food_item
    - brand
    - notes

    Category and location are exact filters.
    """
    df = read_inventory()

    if df.empty:
        return []

    query = query.strip().lower()
    category = category.strip().lower()
    location = location.strip().lower()

    if query:
        searchable_columns = ["food_item", "brand", "notes"]
        mask = pd.Series(False, index=df.index)

        for column in searchable_columns:
            if column in df.columns:
                mask = mask | _safe_text_series(df, column).str.contains(
                    query,
                    regex=False,
                )

        df = df[mask]

    if category and "category" in df.columns:
        df = df[_safe_text_series(df, "category") == category]

    if location and "location" in df.columns:
        df = df[_safe_text_series(df, "location") == location]

    return df_to_records(df)


def get_recent_intake(
    days_back: int = 7,
    meal_type: str = "",
) -> list[dict]:
    """
    Return recent intake history records.

    Optional filters:
    - days_back: number of days back from today to include
    - meal_type: breakfast, lunch, dinner, snack, etc.

    This function reads from user_intake_history.csv.
    """
    df = read_intake_history()

    if df.empty:
        return []

    if "date" not in df.columns:
        logger.warning("Cannot get recent intake because 'date' column is missing.")
        return []

    # Make sure days_back is safe and sensible.
    try:
        days_back = int(days_back)
    except (TypeError, ValueError):
        days_back = 7

    if days_back < 0:
        days_back = 7

    today = date.today()
    start_date = today - timedelta(days=days_back)

    # Parse date column safely.
    df = df.copy()
    df["_parsed_date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    ).dt.date

    # Keep only rows with valid dates inside the recent window.
    df = df[
        (df["_parsed_date"].notna())
        & (df["_parsed_date"] >= start_date)
        & (df["_parsed_date"] <= today)
    ]

    # Optional meal_type filter.
    if meal_type and "meal_type" in df.columns:
        meal_type_clean = meal_type.strip().lower()
        df = df[_safe_text_series(df, "meal_type") == meal_type_clean]

    # Sort newest first.
    sort_columns = ["_parsed_date"]

    if "time" in df.columns:
        sort_columns.append("time")

    df = df.sort_values(
        by=sort_columns,
        ascending=False,
    )

    # Remove helper column before returning.
    df = df.drop(columns=["_parsed_date"], errors="ignore")

    return df_to_records(df)


# ---------------------------------------------------------------------
# Inventory write service functions
# ---------------------------------------------------------------------

def add_inventory_item(
    food_item: str,
    brand: str = "",
    category: str = "",
    location: str = "",
    quantity: float = 0,
    unit: str = "",
    servings_remaining: float = 0,
    stock_status: str = "ok",
    expiry_date: str = "",
    notes: str = "",
) -> dict:
    """
    Add a new item to the active inventory CSV.

    This function:
    - validates required fields
    - generates a stock_id
    - records initial quantity and initial servings
    - records date_added
    - backs up the inventory CSV
    - appends the new row
    - saves the updated CSV
    - returns the created item
    """
    require_non_empty(food_item, "food_item")
    validate_non_negative_number(quantity, "quantity")
    validate_non_negative_number(servings_remaining, "servings_remaining")
    validate_date_or_blank(expiry_date, "expiry_date")

    stock_status = validate_choice(
        stock_status,
        VALID_STOCK_STATUSES,
        "stock_status",
    )

    df = read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)

    existing_ids = df["stock_id"].dropna().astype(str).tolist()
    stock_id = generate_next_id(existing_ids, prefix="inv", width=3)

    quantity_value = float(quantity)
    servings_value = float(servings_remaining)

    new_item = {
        "stock_id": stock_id,
        "food_item": food_item.strip(),
        "brand": brand.strip(),
        "category": category.strip(),
        "location": location.strip(),
        "quantity": quantity_value,
        "unit": unit.strip(),
        "servings_remaining": servings_value,
        "initial_quantity": quantity_value,
        "initial_servings": servings_value,
        "stock_status": stock_status,
        "expiry_date": expiry_date.strip(),
        "date_added": today_iso(),
        "notes": notes.strip(),
    }

    backup_path = backup_csv(INVENTORY_PATH)

    updated_df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
    save_csv(updated_df, INVENTORY_PATH)

    return {
        "success": True,
        "message": "Inventory item added.",
        "item": new_item,
        "backup_created": str(backup_path) if backup_path else None,
    }


def update_inventory_item(
    stock_id: str,
    food_item: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    location: str | None = None,
    quantity: float | None = None,
    unit: str | None = None,
    servings_remaining: float | None = None,
    initial_quantity: float | None = None,
    initial_servings: float | None = None,
    stock_status: str | None = None,
    expiry_date: str | None = None,
    date_added: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    Update an existing item in the active inventory CSV.

    This function:
    - validates the stock_id
    - finds the existing inventory row
    - validates only the fields being updated
    - backs up the inventory CSV
    - updates only fields that are not None
    - saves the updated CSV
    - returns the updated item

    Note:
    - initial_quantity, initial_servings, and date_added are included mainly
      for corrections/migration. Normal day-to-day changes should usually
      update quantity and servings_remaining instead.
    """
    require_non_empty(stock_id, "stock_id")

    updates = {
        "food_item": food_item,
        "brand": brand,
        "category": category,
        "location": location,
        "quantity": quantity,
        "unit": unit,
        "servings_remaining": servings_remaining,
        "initial_quantity": initial_quantity,
        "initial_servings": initial_servings,
        "stock_status": stock_status,
        "expiry_date": expiry_date,
        "date_added": date_added,
        "notes": notes,
    }

    updates = {
        field: value
        for field, value in updates.items()
        if value is not None
    }

    if not updates:
        raise ValueError("At least one field must be provided to update.")

    if "food_item" in updates:
        require_non_empty(updates["food_item"], "food_item")

    for numeric_field in [
        "quantity",
        "servings_remaining",
        "initial_quantity",
        "initial_servings",
    ]:
        if numeric_field in updates:
            validate_non_negative_number(updates[numeric_field], numeric_field)
            updates[numeric_field] = float(updates[numeric_field])

    if "expiry_date" in updates:
        validate_date_or_blank(updates["expiry_date"], "expiry_date")

    if "date_added" in updates:
        validate_date_or_blank(updates["date_added"], "date_added")

    if "stock_status" in updates:
        updates["stock_status"] = validate_choice(
            updates["stock_status"],
            VALID_STOCK_STATUSES,
            "stock_status",
        )

    df = read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)

    matching_rows = (
        df.index[df["stock_id"].astype(str).str.strip() == stock_id.strip()]
        .tolist()
    )

    if not matching_rows:
        raise ValueError(f"No inventory item found with stock_id: {stock_id}")

    row_index = matching_rows[0]

    backup_path = backup_csv(INVENTORY_PATH)

    for field, value in updates.items():
        if isinstance(value, str):
            value = value.strip()

        df.at[row_index, field] = value

    save_csv(df, INVENTORY_PATH)

    updated_item = df.loc[row_index].fillna("").to_dict()

    return {
        "success": True,
        "message": "Inventory item updated.",
        "item": updated_item,
        "backup_created": str(backup_path) if backup_path else None,
    }


def remove_inventory_item(
    stock_id: str,
    removal_type: str = "unknown",
    removal_reason: str = "",
    quantity_wasted: float | None = None,
    servings_wasted: float | None = None,
    tracking_confidence: str = "medium",
    notes: str = "",
) -> dict:
    """
    Remove an item from active inventory.

    If the removal type represents useful food waste behaviour, this function
    creates a food waste record before removing the item from active inventory.

    Waste records are created for:
    - expired
    - spoiled
    - discarded
    - unused
    - overbought
    - did_not_like

    Waste records are not created for:
    - used_up
    - duplicate_entry
    - incorrect_entry
    - test_entry
    - unknown
    """
    require_non_empty(stock_id, "stock_id")

    removal_type = validate_choice(
        removal_type,
        VALID_REMOVAL_TYPES,
        "removal_type",
    )

    tracking_confidence = validate_choice(
        tracking_confidence,
        VALID_TRACKING_CONFIDENCE,
        "tracking_confidence",
    )

    df = read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)

    matching_rows = (
        df.index[df["stock_id"].astype(str).str.strip() == stock_id.strip()]
        .tolist()
    )

    if not matching_rows:
        raise ValueError(f"No inventory item found with stock_id: {stock_id}")

    row_index = matching_rows[0]
    removed_item = df.loc[row_index].fillna("").to_dict()

    waste_record_created = False
    waste_record = None
    waste_backup_path = None

    if removal_type in WASTE_REMOVAL_TYPES:
        current_quantity = to_float(removed_item.get("quantity"), 0.0)
        current_servings = to_float(removed_item.get("servings_remaining"), 0.0)

        initial_quantity = to_float(
            removed_item.get("initial_quantity"),
            current_quantity,
        )
        initial_servings = to_float(
            removed_item.get("initial_servings"),
            current_servings,
        )

        final_quantity_wasted = (
            current_quantity
            if quantity_wasted is None
            else float(quantity_wasted)
        )
        final_servings_wasted = (
            current_servings
            if servings_wasted is None
            else float(servings_wasted)
        )

        validate_non_negative_number(final_quantity_wasted, "quantity_wasted")
        validate_non_negative_number(final_servings_wasted, "servings_wasted")

        estimated_quantity_consumed = max(
            initial_quantity - final_quantity_wasted,
            0,
        )
        estimated_servings_consumed = max(
            initial_servings - final_servings_wasted,
            0,
        )

        waste_df = read_csv_for_write(FOOD_WASTE_PATH, FOOD_WASTE_COLUMNS)

        existing_waste_ids = (
            waste_df["waste_id"]
            .dropna()
            .astype(str)
            .tolist()
        )
        waste_id = generate_next_id(
            existing_waste_ids,
            prefix="waste",
            width=3,
        )

        waste_record = {
            "waste_id": waste_id,
            "stock_id": removed_item.get("stock_id", ""),
            "food_item": removed_item.get("food_item", ""),
            "brand": removed_item.get("brand", ""),
            "category": removed_item.get("category", ""),
            "location": removed_item.get("location", ""),
            "initial_quantity": initial_quantity,
            "initial_unit": removed_item.get("unit", ""),
            "initial_servings": initial_servings,
            "quantity_wasted": final_quantity_wasted,
            "unit": removed_item.get("unit", ""),
            "servings_wasted": final_servings_wasted,
            "estimated_quantity_consumed": estimated_quantity_consumed,
            "estimated_servings_consumed": estimated_servings_consumed,
            "date_added": removed_item.get("date_added", ""),
            "expiry_date": removed_item.get("expiry_date", ""),
            "wasted_at": today_iso(),
            "waste_type": removal_type,
            "waste_reason": removal_reason.strip(),
            "tracking_confidence": tracking_confidence,
            "notes": notes.strip(),
        }

        waste_backup_path = backup_csv(FOOD_WASTE_PATH)
        updated_waste_df = pd.concat(
            [waste_df, pd.DataFrame([waste_record])],
            ignore_index=True,
        )
        save_csv(updated_waste_df, FOOD_WASTE_PATH)
        waste_record_created = True

    inventory_backup_path = backup_csv(INVENTORY_PATH)

    updated_inventory_df = df.drop(index=row_index).reset_index(drop=True)
    save_csv(updated_inventory_df, INVENTORY_PATH)

    if waste_record_created:
        message = "Inventory item removed and a food waste record was created."
    else:
        message = (
            "Inventory item removed from active inventory. "
            "No food waste record was created for this removal type."
        )

    return {
        "success": True,
        "message": message,
        "removed_item": removed_item,
        "waste_record_created": waste_record_created,
        "waste_record": waste_record,
        "inventory_backup_created": (
            str(inventory_backup_path)
            if inventory_backup_path
            else None
        ),
        "waste_backup_created": (
            str(waste_backup_path)
            if waste_backup_path
            else None
        ),
    }
