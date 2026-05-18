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
    INVENTORY_CONSUMPTION_PATH,
    FOOD_WASTE_PATH,
)

from grocery_assistant_mcp.core.schemas import (
    INVENTORY_COLUMNS,
    INTAKE_HISTORY_COLUMNS,
    INTAKE_ITEMS_COLUMNS,
    INVENTORY_CONSUMPTION_COLUMNS,
    FOOD_WASTE_COLUMNS,
)

from grocery_assistant_mcp.core.constants import (
    VALID_STOCK_STATUSES,
    VALID_REMOVAL_TYPES,
    WASTE_REMOVAL_TYPES,
    VALID_TRACKING_CONFIDENCE,
    VALID_MEAL_TYPES,
    VALID_CONSUMPTION_TYPES,
    VALID_CONFIDENCE_LEVELS,
    VALID_YES_NO_UNKNOWN,
    VALID_FINISHED_STATUSES,
)

from grocery_assistant_mcp.core.write_helpers import (
    backup_csv,
    clean_lower_text,
    clean_text,
    generate_next_id,
    read_csv_for_write,
    require_non_empty,
    save_csv,
    validate_choice_or_blank,
    validate_date_or_blank,
    validate_non_negative_fields,
    validate_non_negative_number,
    validate_required_choice,
    validate_required_date,
    validate_time_or_blank,
    validate_int_range,
)

logger = logging.getLogger("grocery_mcp.grocery_data")


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


def should_create_food_waste_record(removal_type: str) -> bool:
    """
    Return True when a removal type should create a food waste record.
    """
    removal_type = validate_required_choice(
        removal_type,
        VALID_REMOVAL_TYPES,
        "removal_type",
    )
    return removal_type in WASTE_REMOVAL_TYPES


def infer_stock_status(
    quantity: float,
    servings_remaining: float,
    stock_status: str,
) -> str:
    """
    Infer a safer stock_status from quantity and servings.

    Canonical Version 1.3 statuses:
    - in_stock: usable stock is available
    - low: usable stock is running low
    - very_low: usable stock is nearly depleted
    - out: no usable stock remains, but the row may remain as a restock signal
    - expired: food is expired but still physically present

    This is intentionally conservative:
    - quantity=0 and servings=0 changes available-like statuses to "out"
    - positive quantity or servings changes "out" to "low"
    - explicit "expired" is not silently overwritten
    """
    stock_status = clean_lower_text(stock_status, "stock_status") or "in_stock"

    if quantity == 0 and servings_remaining == 0:
        if stock_status in {"in_stock", "low", "very_low"}:
            return "out"

    if quantity > 0 or servings_remaining > 0:
        if stock_status == "out":
            return "low"

    return stock_status


def validate_inventory_stock_consistency(
    quantity: float,
    servings_remaining: float,
    stock_status: str,
) -> None:
    """
    Validate that quantity, servings_remaining, and stock_status are compatible.

    This catches impossible or risky states while still allowing useful grocery
    tracking states such as expired food that is still physically present.
    """
    validate_non_negative_number(quantity, "quantity")
    validate_non_negative_number(servings_remaining, "servings_remaining")

    if stock_status == "in_stock" and quantity == 0 and servings_remaining == 0:
        raise ValueError(
            "Items with quantity=0 and servings_remaining=0 should not have "
            "stock_status='in_stock'."
        )

    if stock_status == "expired" and quantity == 0 and servings_remaining == 0:
        raise ValueError(
            "Expired items with no quantity or servings remaining should be removed "
            "with removal_type='expired' instead of kept as active inventory."
        )


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
    Read user_inventory.csv as the user's tracked grocery stock state.

    This file supports current grocery awareness and future personalization.
    It may include food that is currently available, running low, empty/out
    of stock but intentionally kept as a restock signal, or expired but still
    physically present.

    Items should remain here when they are still useful for shopping,
    planning, or habit recognition.

    Items should be removed only when they are no longer useful to track,
    were entered incorrectly, are duplicates/test data, or have been discarded
    as waste.
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


def read_inventory_consumption() -> pd.DataFrame:
    """
    Read the inventory consumption event log.

    This file records inventory usage events, including inventory-only
    consumption and intake-linked consumption.
    """
    return read_csv_file(INVENTORY_CONSUMPTION_PATH)


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
    Return tracked grocery inventory records as JSON-ready dictionaries.

    Tracked inventory includes items that are useful for current or future
    grocery decisions. This can include:
    - available items
    - low or very low stock items
    - empty/out-of-stock items kept as shopping reminders
    - expired items still physically present

    Keeping some out-of-stock items is intentional. It can help the assistant
    recognize common staples, restock patterns, frequently used ingredients,
    and lower-priority items that do not require urgent replacement.

    Optional filters:
    - category: return only items from a category such as pantry, dairy, produce, or protein
    - low_stock_only: return items marked low, very low, empty, or out
    """
    df = read_inventory()

    if df.empty:
        return []

    category_clean = clean_lower_text(category)

    if category_clean and "category" in df.columns:
        df = df[_safe_text_series(df, "category") == category_clean]

    if low_stock_only and "stock_status" in df.columns:
        low_statuses = ["low", "very_low", "out"]
        df = df[_safe_text_series(df, "stock_status").isin(low_statuses)]

    return df_to_records(df)

def list_intake_history() -> list[dict]:
    """
    Return intake history records as JSON-ready dictionaries.

    This is intended for MCP resources and read-only tools.
    """
    df = read_intake_history()

    if df.empty:
        return []

    return df_to_records(df)


def list_intake_items() -> list[dict]:
    """
    Return intake item records as JSON-ready dictionaries.

    This is intended for MCP resources and read-only tools.
    """
    df = read_intake_items()

    if df.empty:
        return []

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

    This supports grocery://food-waste and grocery://food-waste/expired.
    """
    df = read_food_waste()

    if df.empty:
        return []

    waste_type = clean_lower_text(waste_type, "waste_type")
    category = clean_lower_text(category, "category")

    if waste_type and "waste_type" in df.columns:
        df = df[_safe_text_series(df, "waste_type") == waste_type]

    if category and "category" in df.columns:
        df = df[_safe_text_series(df, "category") == category]

    return df_to_records(df)


def list_inventory_consumption(
    stock_id: str = "",
    intake_id: str = "",
    intake_item_id: str = "",
    consumption_type: str = "",
) -> list[dict]:
    """
    Return inventory consumption event records.

    Optional filters:
    - stock_id
    - intake_id
    - intake_item_id
    - consumption_type
    """
    df = read_csv_for_write(
        INVENTORY_CONSUMPTION_PATH,
        INVENTORY_CONSUMPTION_COLUMNS,
    )

    if df.empty:
        return []

    stock_id = clean_text(stock_id, "stock_id")
    intake_id = clean_text(intake_id, "intake_id")
    intake_item_id = clean_text(intake_item_id, "intake_item_id")
    consumption_type = clean_lower_text(consumption_type, "consumption_type")

    if stock_id:
        df = df[_safe_text_series(df, "stock_id") == stock_id.lower()]

    if intake_id:
        df = df[_safe_text_series(df, "intake_id") == intake_id.lower()]

    if intake_item_id:
        df = df[_safe_text_series(df, "intake_item_id") == intake_item_id.lower()]

    if consumption_type:
        df = df[_safe_text_series(df, "consumption_type") == consumption_type]

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
    """
    date = validate_required_date(date, "date")

    history_df = read_intake_history()
    items_df = read_intake_items()

    if history_df.empty or "date" not in history_df.columns:
        day_history = pd.DataFrame()
    else:
        day_history = history_df[history_df["date"].astype(str) == date].copy()

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

    nutrition_totals = {output_name: 0.0 for output_name in item_nutrition_columns.keys()}
    missing_nutrition_counts = {output_name: 0 for output_name in item_nutrition_columns.keys()}

    meal_ids_using_item_totals = []
    meal_ids_using_meal_totals = []

    if not day_items.empty and "intake_id" in day_items.columns:
        item_groups = {
            str(intake_id).strip(): group.copy()
            for intake_id, group in day_items.groupby(
                day_items["intake_id"].fillna("").astype(str).str.strip()
            )
        }
    else:
        item_groups = {}

    for _, meal_row in day_history.iterrows():
        intake_id = str(meal_row.get("intake_id", "")).strip()
        item_group = item_groups.get(intake_id)

        if item_group is not None and not item_group.empty:
            meal_ids_using_item_totals.append(intake_id)

            for output_name, source_column in item_nutrition_columns.items():
                if source_column in item_group.columns:
                    numeric_values = pd.to_numeric(item_group[source_column], errors="coerce")
                    nutrition_totals[output_name] += float(numeric_values.fillna(0).sum())
                    missing_nutrition_counts[output_name] += int(numeric_values.isna().sum())
                else:
                    missing_nutrition_counts[output_name] += int(len(item_group))
        else:
            meal_ids_using_meal_totals.append(intake_id)

            for output_name, source_column in meal_nutrition_columns.items():
                if source_column in day_history.columns:
                    value = pd.to_numeric(pd.Series([meal_row.get(source_column)]), errors="coerce").iloc[0]
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

def search_intake(
    query: str = "",
    intake_id: str = "",
    intake_item_id: str = "",
    date: str = "",
    date_from: str = "",
    date_to: str = "",
    meal_type: str = "",
    source: str = "",
    stock_id: str = "",
    category: str = "",
    limit: int = 20,
) -> dict:
    """
    Search intake parent entries and child item records.

    This is a Version 1.2 read-only helper for safe editing and cleanup.
    It helps locate intake_id and intake_item_id values before update/remove
    tools are called.

    The function searches:
    - user_intake_history.csv for parent meal/eating-event records
    - user_intake_items.csv for child ingredient/component records

    It also returns relationship context:
    - parent entries include child_item_count and can_remove_entry
    - child items include parent date, time, meal type, and meal name
    """
    query = _optional_clean_text(query, "query")
    intake_id = _optional_clean_text(intake_id, "intake_id")
    intake_item_id = _optional_clean_text(intake_item_id, "intake_item_id")
    date = _optional_clean_text(date, "date")
    date_from = _optional_clean_text(date_from, "date_from")
    date_to = _optional_clean_text(date_to, "date_to")
    meal_type = _optional_clean_text(meal_type, "meal_type")
    source = _optional_clean_text(source, "source")
    stock_id = _optional_clean_text(stock_id, "stock_id")
    category = _optional_clean_text(category, "category")
    limit = _normalise_search_limit(limit)

    if date:
        validate_required_date(date, "date")

    if date_from:
        validate_required_date(date_from, "date_from")

    if date_to:
        validate_required_date(date_to, "date_to")

    if meal_type:
        meal_type = validate_required_choice(
            meal_type,
            VALID_MEAL_TYPES,
            "meal_type",
        )

    history_df = read_csv_for_write(
        INTAKE_HISTORY_PATH,
        INTAKE_HISTORY_COLUMNS,
    ).fillna("")

    items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    ).fillna("")

    # Ensure expected columns are string-safe for filtering.
    for df in [history_df, items_df]:
        for column in df.columns:
            df[column] = df[column].fillna("").astype(str)

    # ------------------------------------------------------------------
    # Build parent context for child rows
    # ------------------------------------------------------------------

    parent_context_columns = [
        "intake_id",
        "date",
        "time",
        "meal_type",
        "meal_name",
        "source",
    ]

    existing_parent_context_columns = [
        column for column in parent_context_columns if column in history_df.columns
    ]

    if existing_parent_context_columns:
        parent_context_df = history_df[existing_parent_context_columns].copy()
    else:
        parent_context_df = pd.DataFrame(columns=parent_context_columns)

    parent_context_df = parent_context_df.rename(
        columns={
            "date": "parent_date",
            "time": "parent_time",
            "meal_type": "parent_meal_type",
            "meal_name": "parent_meal_name",
            "source": "parent_source",
        }
    )

    if not items_df.empty and "intake_id" in items_df.columns:
        items_with_parent_df = items_df.merge(
            parent_context_df,
            how="left",
            on="intake_id",
        ).fillna("")
    else:
        items_with_parent_df = items_df.copy()

        for column in [
            "parent_date",
            "parent_time",
            "parent_meal_type",
            "parent_meal_name",
            "parent_source",
        ]:
            items_with_parent_df[column] = ""

    # ------------------------------------------------------------------
    # Parent entry filtering
    # ------------------------------------------------------------------

    if history_df.empty:
        entry_mask = pd.Series([], dtype=bool)
    else:
        entry_mask = pd.Series([True] * len(history_df), index=history_df.index)

    if intake_id:
        entry_mask = entry_mask & _exact_text_mask(history_df, "intake_id", intake_id)

    if query:
        entry_query_columns = [
            "intake_id",
            "meal_name",
            "meal_description",
            "source",
            "amount_eaten",
            "portion_confidence",
            "nutrition_confidence",
            "was_finished",
            "leftovers_created",
            "hunger_before",
            "hunger_after",
            "notes",
        ]
        entry_mask = entry_mask & _contains_query_mask(
            history_df,
            entry_query_columns,
            query,
        )

    if date:
        entry_mask = entry_mask & _exact_text_mask(history_df, "date", date)

    if date_from and "date" in history_df.columns:
        entry_mask = entry_mask & (history_df["date"].astype(str) >= date_from)

    if date_to and "date" in history_df.columns:
        entry_mask = entry_mask & (history_df["date"].astype(str) <= date_to)

    if meal_type:
        entry_mask = entry_mask & _exact_text_mask(history_df, "meal_type", meal_type)

    if source:
        entry_mask = entry_mask & _exact_text_mask(history_df, "source", source)

    matching_entries_df = history_df[entry_mask].copy()

    # ------------------------------------------------------------------
    # Child item filtering
    # ------------------------------------------------------------------

    if items_with_parent_df.empty:
        item_mask = pd.Series([], dtype=bool)
    else:
        item_mask = pd.Series(
            [True] * len(items_with_parent_df),
            index=items_with_parent_df.index,
        )

    if intake_id:
        item_mask = item_mask & _exact_text_mask(
            items_with_parent_df,
            "intake_id",
            intake_id,
        )

    if intake_item_id:
        item_mask = item_mask & _exact_text_mask(
            items_with_parent_df,
            "intake_item_id",
            intake_item_id,
        )

    if query:
        item_query_columns = [
            "intake_item_id",
            "intake_id",
            "food_item",
            "brand",
            "category",
            "source",
            "stock_id",
            "amount_eaten",
            "quantity_used",
            "unit",
            "servings_used",
            "nutrition_confidence",
            "notes",
        ]   
        item_mask = item_mask & _contains_query_mask(
            items_with_parent_df,
            item_query_columns,
            query,
        )

    if date:
        item_mask = item_mask & _exact_text_mask(
            items_with_parent_df,
            "parent_date",
            date,
        )

    if date_from and "parent_date" in items_with_parent_df.columns:
        item_mask = item_mask & (
            items_with_parent_df["parent_date"].astype(str) >= date_from
        )

    if date_to and "parent_date" in items_with_parent_df.columns:
        item_mask = item_mask & (
            items_with_parent_df["parent_date"].astype(str) <= date_to
        )

    if meal_type:
        item_mask = item_mask & _exact_text_mask(
            items_with_parent_df,
            "parent_meal_type",
            meal_type,
        )

    if source:
        child_source_mask = _exact_text_mask(items_with_parent_df, "source", source)
        parent_source_mask = _exact_text_mask(
            items_with_parent_df,
            "parent_source",
            source,
        )
        item_mask = item_mask & (child_source_mask | parent_source_mask)

    if stock_id:
        item_mask = item_mask & _exact_text_mask(items_with_parent_df, "stock_id", stock_id)

    if category:
        item_mask = item_mask & _exact_text_mask(items_with_parent_df, "category", category)

    matching_items_df = items_with_parent_df[item_mask].copy()

    # ------------------------------------------------------------------
    # If searching by intake_item_id, include its parent entry for context.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Include parent entries for matched child item rows.
    #
    # This supports child-side searches such as:
    # - stock_id="inv_001"
    # - category="protein"
    # - intake_item_id="intake_item_001"
    # - query="beef mince"
    #
    # If a child item matches, its parent meal should also be returned so
    # the user can safely inspect the relationship before editing/removing.
    # ------------------------------------------------------------------

    filters_used = any(
        [
            query,
            intake_id,
            intake_item_id,
            date,
            date_from,
            date_to,
            meal_type,
            source,
            stock_id,
            category,
        ]
    )

    parent_filters_used = any(
        [
            query,
            intake_id,
            date,
            date_from,
            date_to,
            meal_type,
            source,
        ]
    )

    if not matching_items_df.empty and "intake_id" in matching_items_df.columns:
        child_parent_ids = set(
            matching_items_df["intake_id"].fillna("").astype(str).str.strip()
        )

        child_parent_rows_df = history_df[
            history_df["intake_id"].fillna("").astype(str).str.strip().isin(
                child_parent_ids
            )
        ].copy()
    else:
        child_parent_rows_df = pd.DataFrame(columns=history_df.columns)

    if filters_used and not child_parent_rows_df.empty:
        if parent_filters_used:
            matching_entries_df = pd.concat(
                [matching_entries_df, child_parent_rows_df],
                ignore_index=True,
            ).drop_duplicates(subset=["intake_id"])
        else:
            matching_entries_df = child_parent_rows_df.copy()

    if filters_used and not parent_filters_used and child_parent_rows_df.empty:
        matching_entries_df = history_df.iloc[0:0].copy()

    # ------------------------------------------------------------------
    # Add relationship metadata to parent entries.
    # ------------------------------------------------------------------

    if not items_df.empty and "intake_id" in items_df.columns:
        child_counts = items_df.groupby("intake_id").size().to_dict()
    else:
        child_counts = {}

    if not matching_entries_df.empty:
        matching_entries_df["record_type"] = "intake_entry"
        matching_entries_df["child_item_count"] = matching_entries_df["intake_id"].map(
            child_counts
        ).fillna(0).astype(int)
        matching_entries_df["can_remove_entry"] = (
            matching_entries_df["child_item_count"] == 0
        )

    if not matching_items_df.empty:
        matching_items_df["record_type"] = "intake_item"

    # ------------------------------------------------------------------
    # Sort most recent first and limit output.
    # ------------------------------------------------------------------

    if not matching_entries_df.empty:
        sort_columns = [
            column for column in ["date", "time", "intake_id"] if column in matching_entries_df.columns
        ]
        matching_entries_df = matching_entries_df.sort_values(
            by=sort_columns,
            ascending=False,
        ).head(limit)

    if not matching_items_df.empty:
        sort_columns = [
            column
            for column in ["parent_date", "parent_time", "intake_item_id"]
            if column in matching_items_df.columns
        ]
        matching_items_df = matching_items_df.sort_values(
            by=sort_columns,
            ascending=False,
        ).head(limit)

    return {
        "success": True,
        "criteria": {
            "query": query,
            "intake_id": intake_id,
            "intake_item_id": intake_item_id,
            "date": date,
            "date_from": date_from,
            "date_to": date_to,
            "meal_type": meal_type,
            "source": source,
            "stock_id": stock_id,
            "category": category,
            "limit": limit,
        },
        "entry_count": int(len(matching_entries_df)),
        "item_count": int(len(matching_items_df)),
        "matching_entries": df_to_records(matching_entries_df),
        "matching_items": df_to_records(matching_items_df),
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
    - days_back: number of days back from today to include, 0 to 365
    - meal_type: breakfast, lunch, dinner, snack, etc.
    """
    days_back = validate_int_range(
        days_back,
        field_name="days_back",
        minimum=0,
        maximum=365,
    )

    meal_type = validate_choice_or_blank(
        meal_type,
        VALID_MEAL_TYPES,
        "meal_type",
        default="",
    )

    df = read_intake_history()

    if df.empty:
        return []

    if "date" not in df.columns:
        logger.warning("Cannot get recent intake because 'date' column is missing.")
        return []

    today = date.today()
    start_date = today - timedelta(days=days_back)

    df = df.copy()
    df["_parsed_date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    df = df[
        (df["_parsed_date"].notna())
        & (df["_parsed_date"] >= start_date)
        & (df["_parsed_date"] <= today)
    ]

    if meal_type and "meal_type" in df.columns:
        df = df[_safe_text_series(df, "meal_type") == meal_type]

    sort_columns = ["_parsed_date"]

    if "time" in df.columns:
        sort_columns.append("time")

    df = df.sort_values(by=sort_columns, ascending=False)
    df = df.drop(columns=["_parsed_date"], errors="ignore")

    return df_to_records(df)

def _normalise_search_limit(limit: int, default: int = 20, maximum: int = 100) -> int:
    """
    Normalise a user-provided search limit.

    The cap prevents very large MCP responses while still allowing broader
    inspection when needed.
    """
    if limit is None:
        return default

    try:
        limit_value = int(limit)
    except (TypeError, ValueError):
        raise ValueError("limit must be a positive integer.")

    if limit_value < 1:
        raise ValueError("limit must be at least 1.")

    return min(limit_value, maximum)


def _optional_clean_text(value: str | None, field_name: str) -> str:
    """
    Clean optional text search/filter values.
    """
    if value is None:
        return ""

    return str(value).strip()


def _contains_query_mask(df: pd.DataFrame, columns: list[str], query: str) -> pd.Series:
    """
    Return a boolean mask where any selected column contains the query.

    Matching is case-insensitive and literal, not regex-based.
    """
    if df.empty:
        return pd.Series([], dtype=bool)

    if not query:
        return pd.Series([True] * len(df), index=df.index)

    query = query.lower().strip()
    existing_columns = [column for column in columns if column in df.columns]

    if not existing_columns:
        return pd.Series([False] * len(df), index=df.index)

    mask = pd.Series([False] * len(df), index=df.index)

    for column in existing_columns:
        column_text = df[column].fillna("").astype(str).str.lower()
        mask = mask | column_text.str.contains(query, regex=False, na=False)

    return mask


def _exact_text_mask(df: pd.DataFrame, column: str, value: str) -> pd.Series:
    """
    Return a case-insensitive exact-match mask for a text column.
    """
    if df.empty:
        return pd.Series([], dtype=bool)

    if not value:
        return pd.Series([True] * len(df), index=df.index)

    if column not in df.columns:
        return pd.Series([False] * len(df), index=df.index)

    return df[column].fillna("").astype(str).str.strip().str.lower() == value.lower()


def save_related_csv_updates(
    operations: list[tuple[str, Path, pd.DataFrame, pd.DataFrame]],
) -> dict[str, str | None]:
    """
    Save multiple related CSV updates with best-effort rollback.

    Each operation is:
    - logical name
    - CSV path
    - original DataFrame
    - updated DataFrame

    This does not replace a real database transaction, but it reduces the risk
    of leaving related CSV files out of sync during multi-file workflows.
    """
    backup_paths: dict[str, str | None] = {}

    try:
        for name, path, _original_df, _updated_df in operations:
            backup_path = backup_csv(path)
            backup_paths[name] = str(backup_path) if backup_path else None

        for _name, path, _original_df, updated_df in operations:
            save_csv(updated_df, path)

    except Exception as exc:
        try:
            for _name, path, original_df, _updated_df in operations:
                save_csv(original_df, path)
        except Exception as rollback_exc:
            raise RuntimeError(
                "Failed to save related CSV updates, and rollback also failed."
            ) from rollback_exc

        raise RuntimeError(
            "Failed to save related CSV updates. Original CSV state was restored."
        ) from exc

    return backup_paths

# ---------------------------------------------------------------------
# Intake write service functions
# ---------------------------------------------------------------------

def id_exists(
    df: pd.DataFrame,
    id_column: str,
    id_value: str,
) -> bool:
    """
    Return True if an ID exists in a DataFrame.
    """
    if df.empty or id_column not in df.columns:
        return False

    cleaned_id = clean_text(id_value)

    return (
        df[id_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .eq(cleaned_id)
        .any()
    )


def require_existing_id(
    df: pd.DataFrame,
    id_column: str,
    id_value: str,
    entity_name: str,
) -> str:
    """
    Validate that an ID exists in a DataFrame.

    Returns the cleaned ID.
    """
    cleaned_id = clean_text(id_value, id_column, required=True)

    if id_column not in df.columns:
        raise ValueError(
            f"Cannot validate {entity_name} because '{id_column}' column is missing."
        )

    if not id_exists(df, id_column, cleaned_id):
        raise ValueError(f"No {entity_name} found with {id_column}: {cleaned_id}")

    return cleaned_id


def intake_id_exists(intake_id: str) -> bool:
    """
    Return True if an intake history record exists for the supplied intake_id.

    This protects user_intake_items.csv from orphan rows.
    """
    cleaned_id = clean_text(intake_id, "intake_id", required=True)

    history_df = read_csv_for_write(
        INTAKE_HISTORY_PATH,
        INTAKE_HISTORY_COLUMNS,
    )

    return id_exists(history_df, "intake_id", cleaned_id)


def require_existing_intake_id(intake_id: str) -> str:
    """
    Validate that an intake_id exists in user_intake_history.csv.
    """
    history_df = read_csv_for_write(
        INTAKE_HISTORY_PATH,
        INTAKE_HISTORY_COLUMNS,
    )

    return require_existing_id(
        df=history_df,
        id_column="intake_id",
        id_value=intake_id,
        entity_name="intake entry",
    )


def require_existing_stock_id(stock_id: str) -> str:
    """
    Validate that a stock_id exists in user_inventory.csv.

    This is useful for future inventory deduction workflows.
    """
    inventory_df = read_csv_for_write(
        INVENTORY_PATH,
        INVENTORY_COLUMNS,
    )

    return require_existing_id(
        df=inventory_df,
        id_column="stock_id",
        id_value=stock_id,
        entity_name="inventory item",
    )


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
    Add a meal or eating event to user_intake_history.csv.

    This function records the meal-level intake event only. It does not
    automatically deduct inventory, create leftovers, or create food waste.

    Use add_intake_item() to attach optional ingredient/component rows to
    this meal through intake_id.
    """
    date = clean_text(date, "date", required=True)
    meal_name = clean_text(meal_name, "meal_name", required=True)
    time = clean_text(time, "time")
    meal_description = clean_text(meal_description)
    source = clean_text(source)
    amount_eaten = clean_text(amount_eaten)
    hunger_before = clean_text(hunger_before)
    hunger_after = clean_text(hunger_after)
    notes = clean_text(notes)

    validate_date_or_blank(date, "date")
    validate_time_or_blank(time, "time")

    meal_type = validate_required_choice(
        meal_type,
        VALID_MEAL_TYPES,
        "meal_type",
    )

    portion_confidence = validate_choice_or_blank(
        portion_confidence,
        VALID_CONFIDENCE_LEVELS,
        "portion_confidence",
        default="unknown",
    )

    nutrition_confidence = validate_choice_or_blank(
        nutrition_confidence,
        VALID_CONFIDENCE_LEVELS,
        "nutrition_confidence",
        default="unknown",
    )

    was_finished = validate_choice_or_blank(
        was_finished,
        VALID_FINISHED_STATUSES,
        "was_finished",
        default="unknown",
    )

    leftovers_created = validate_choice_or_blank(
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

    df = read_csv_for_write(INTAKE_HISTORY_PATH, INTAKE_HISTORY_COLUMNS)

    existing_ids = df["intake_id"].dropna().astype(str).tolist()
    intake_id = generate_next_id(existing_ids, prefix="intake", width=3)

    new_entry = {
        "intake_id": intake_id,
        "date": date,
        "time": time,
        "meal_type": meal_type,
        "meal_name": meal_name,
        "meal_description": meal_description,
        "source": source,
        "amount_eaten": amount_eaten,
        "portion_confidence": portion_confidence,
        "total_calories_estimate": numeric_values["total_calories_estimate"],
        "total_protein_g_estimate": numeric_values["total_protein_g_estimate"],
        "total_carbs_g_estimate": numeric_values["total_carbs_g_estimate"],
        "total_fat_g_estimate": numeric_values["total_fat_g_estimate"],
        "total_fibre_g_estimate": numeric_values["total_fibre_g_estimate"],
        "total_sugar_g_estimate": numeric_values["total_sugar_g_estimate"],
        "total_sodium_mg_estimate": numeric_values["total_sodium_mg_estimate"],
        "nutrition_confidence": nutrition_confidence,
        "was_finished": was_finished,
        "leftovers_created": leftovers_created,
        "hunger_before": hunger_before,
        "hunger_after": hunger_after,
        "notes": notes,
    }

    backup_path = backup_csv(INTAKE_HISTORY_PATH)

    updated_df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_csv(updated_df, INTAKE_HISTORY_PATH)

    return {
        "success": True,
        "message": "Intake entry added.",
        "item": new_entry,
        "backup_created": str(backup_path) if backup_path else None,
    }


def update_intake_entry(
    intake_id: str,
    date: str | None = None,
    time: str | None = None,
    meal_type: str | None = None,
    meal_name: str | None = None,
    meal_description: str | None = None,
    source: str | None = None,
    amount_eaten: str | None = None,
    portion_confidence: str | None = None,
    total_calories_estimate: float | None = None,
    total_protein_g_estimate: float | None = None,
    total_carbs_g_estimate: float | None = None,
    total_fat_g_estimate: float | None = None,
    total_fibre_g_estimate: float | None = None,
    total_sugar_g_estimate: float | None = None,
    total_sodium_mg_estimate: float | None = None,
    nutrition_confidence: str | None = None,
    was_finished: str | None = None,
    leftovers_created: str | None = None,
    hunger_before: str | None = None,
    hunger_after: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    Update an existing parent intake entry.

    Fields left as None are not changed. String fields may be intentionally
    cleared by passing an empty string, except required fields such as date
    and meal_name.
    """
    intake_id = clean_text(intake_id, "intake_id", required=True)

    updates = {
        "date": date,
        "time": time,
        "meal_type": meal_type,
        "meal_name": meal_name,
        "meal_description": meal_description,
        "source": source,
        "amount_eaten": amount_eaten,
        "portion_confidence": portion_confidence,
        "total_calories_estimate": total_calories_estimate,
        "total_protein_g_estimate": total_protein_g_estimate,
        "total_carbs_g_estimate": total_carbs_g_estimate,
        "total_fat_g_estimate": total_fat_g_estimate,
        "total_fibre_g_estimate": total_fibre_g_estimate,
        "total_sugar_g_estimate": total_sugar_g_estimate,
        "total_sodium_mg_estimate": total_sodium_mg_estimate,
        "nutrition_confidence": nutrition_confidence,
        "was_finished": was_finished,
        "leftovers_created": leftovers_created,
        "hunger_before": hunger_before,
        "hunger_after": hunger_after,
        "notes": notes,
    }

    updates = {field: value for field, value in updates.items() if value is not None}

    if not updates:
        raise ValueError("At least one field must be provided to update.")

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
        if field in updates:
            updates[field] = clean_text(
                updates[field],
                field,
                required=(field in {"date", "meal_name"}),
            )

    if "date" in updates:
        validate_required_date(updates["date"], "date")

    if "time" in updates:
        validate_time_or_blank(updates["time"], "time")

    if "meal_type" in updates:
        updates["meal_type"] = validate_required_choice(
            updates["meal_type"],
            VALID_MEAL_TYPES,
            "meal_type",
        )

    if "portion_confidence" in updates:
        updates["portion_confidence"] = validate_choice_or_blank(
            updates["portion_confidence"],
            VALID_CONFIDENCE_LEVELS,
            "portion_confidence",
            default="unknown",
        )

    if "nutrition_confidence" in updates:
        updates["nutrition_confidence"] = validate_choice_or_blank(
            updates["nutrition_confidence"],
            VALID_CONFIDENCE_LEVELS,
            "nutrition_confidence",
            default="unknown",
        )

    if "was_finished" in updates:
        updates["was_finished"] = validate_choice_or_blank(
            updates["was_finished"],
            VALID_FINISHED_STATUSES,
            "was_finished",
            default="unknown",
        )

    if "leftovers_created" in updates:
        updates["leftovers_created"] = validate_choice_or_blank(
            updates["leftovers_created"],
            VALID_YES_NO_UNKNOWN,
            "leftovers_created",
            default="unknown",
        )

    numeric_fields = [
        "total_calories_estimate",
        "total_protein_g_estimate",
        "total_carbs_g_estimate",
        "total_fat_g_estimate",
        "total_fibre_g_estimate",
        "total_sugar_g_estimate",
        "total_sodium_mg_estimate",
    ]

    for field in numeric_fields:
        if field in updates:
            updates[field] = validate_non_negative_number(updates[field], field)

    df = read_csv_for_write(INTAKE_HISTORY_PATH, INTAKE_HISTORY_COLUMNS)

    matching_rows = df.index[
        df["intake_id"].astype(str).str.strip() == intake_id
    ].tolist()

    if not matching_rows:
        raise ValueError(f"No intake entry found with intake_id: {intake_id}")

    row_index = matching_rows[0]

    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce").astype("float64")

    for field, value in updates.items():
        df.at[row_index, field] = value

    backup_path = backup_csv(INTAKE_HISTORY_PATH)
    save_csv(df, INTAKE_HISTORY_PATH)

    updated_entry = df.loc[row_index].fillna("").to_dict()

    return {
        "success": True,
        "message": "Intake entry updated.",
        "item": updated_entry,
        "backup_created": str(backup_path) if backup_path else None,
    }


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
    Add an ingredient, food item, or component to user_intake_items.csv.

    Each row belongs to a parent meal/eating event in user_intake_history.csv
    through intake_id. Optional stock_id values are validated if supplied.
    """
    intake_id = require_existing_intake_id(intake_id)

    food_item = clean_text(food_item, "food_item", required=True)
    brand = clean_text(brand, "brand")
    category = clean_text(category, "category")
    source = clean_text(source, "source")
    stock_id = clean_text(stock_id, "stock_id")
    amount_eaten = clean_text(amount_eaten, "amount_eaten")
    unit = clean_text(unit, "unit")
    notes = clean_text(notes, "notes")

    if stock_id:
        stock_id = require_existing_stock_id(stock_id)

    nutrition_confidence = validate_choice_or_blank(
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

    df = read_csv_for_write(INTAKE_ITEMS_PATH, INTAKE_ITEMS_COLUMNS)

    existing_ids = df["intake_item_id"].dropna().astype(str).tolist()
    intake_item_id = generate_next_id(existing_ids, prefix="intake_item", width=3)

    new_item = {
        "intake_item_id": intake_item_id,
        "intake_id": intake_id,
        "food_item": food_item,
        "brand": brand,
        "category": category,
        "source": source,
        "stock_id": stock_id,
        "amount_eaten": amount_eaten,
        "quantity_used": numeric_values["quantity_used"],
        "unit": unit,
        "servings_used": numeric_values["servings_used"],
        "calories_estimate": numeric_values["calories_estimate"],
        "protein_g_estimate": numeric_values["protein_g_estimate"],
        "carbs_g_estimate": numeric_values["carbs_g_estimate"],
        "fat_g_estimate": numeric_values["fat_g_estimate"],
        "fibre_g_estimate": numeric_values["fibre_g_estimate"],
        "sugar_g_estimate": numeric_values["sugar_g_estimate"],
        "sodium_mg_estimate": numeric_values["sodium_mg_estimate"],
        "nutrition_confidence": nutrition_confidence,
        "notes": notes,
    }

    backup_path = backup_csv(INTAKE_ITEMS_PATH)
    updated_df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
    save_csv(updated_df, INTAKE_ITEMS_PATH)

    return {
        "success": True,
        "message": "Intake item added.",
        "item": new_item,
        "backup_created": str(backup_path) if backup_path else None,
    }


def update_intake_item(
    intake_item_id: str,
    intake_id: str | None = None,
    food_item: str | None = None,
    brand: str | None = None,
    category: str | None = None,
    source: str | None = None,
    stock_id: str | None = None,
    amount_eaten: str | None = None,
    quantity_used: float | None = None,
    unit: str | None = None,
    servings_used: float | None = None,
    calories_estimate: float | None = None,
    protein_g_estimate: float | None = None,
    carbs_g_estimate: float | None = None,
    fat_g_estimate: float | None = None,
    fibre_g_estimate: float | None = None,
    sugar_g_estimate: float | None = None,
    sodium_mg_estimate: float | None = None,
    nutrition_confidence: str | None = None,
    notes: str | None = None,
) -> dict:
    """
    Update an existing child intake item.

    Fields left as None are not changed. If intake_id is changed, the new
    parent intake entry must already exist. If stock_id is changed and not
    blank, the stock_id must already exist.
    """
    intake_item_id = clean_text(intake_item_id, "intake_item_id", required=True)

    updates = {
        "intake_id": intake_id,
        "food_item": food_item,
        "brand": brand,
        "category": category,
        "source": source,
        "stock_id": stock_id,
        "amount_eaten": amount_eaten,
        "quantity_used": quantity_used,
        "unit": unit,
        "servings_used": servings_used,
        "calories_estimate": calories_estimate,
        "protein_g_estimate": protein_g_estimate,
        "carbs_g_estimate": carbs_g_estimate,
        "fat_g_estimate": fat_g_estimate,
        "fibre_g_estimate": fibre_g_estimate,
        "sugar_g_estimate": sugar_g_estimate,
        "sodium_mg_estimate": sodium_mg_estimate,
        "nutrition_confidence": nutrition_confidence,
        "notes": notes,
    }

    updates = {field: value for field, value in updates.items() if value is not None}

    if not updates:
        raise ValueError("At least one field must be provided to update.")

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
        if field in updates:
            updates[field] = clean_text(
                updates[field],
                field,
                required=(field in {"intake_id", "food_item"}),
            )

    if "intake_id" in updates:
        updates["intake_id"] = require_existing_intake_id(updates["intake_id"])

    if "stock_id" in updates and updates["stock_id"]:
        updates["stock_id"] = require_existing_stock_id(updates["stock_id"])

    if "nutrition_confidence" in updates:
        updates["nutrition_confidence"] = validate_choice_or_blank(
            updates["nutrition_confidence"],
            VALID_CONFIDENCE_LEVELS,
            "nutrition_confidence",
            default="unknown",
        )

    numeric_fields = [
        "servings_used",
        "quantity_used",
        "calories_estimate",
        "protein_g_estimate",
        "carbs_g_estimate",
        "fat_g_estimate",
        "fibre_g_estimate",
        "sugar_g_estimate",
        "sodium_mg_estimate",
    ]

    for field in numeric_fields:
        if field in updates:
            updates[field] = validate_non_negative_number(updates[field], field)

    df = read_csv_for_write(INTAKE_ITEMS_PATH, INTAKE_ITEMS_COLUMNS)

    matching_rows = df.index[
        df["intake_item_id"].astype(str).str.strip() == intake_item_id
    ].tolist()

    if not matching_rows:
        raise ValueError(f"No intake item found with intake_item_id: {intake_item_id}")

    row_index = matching_rows[0]

    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce").astype("float64")

    for field, value in updates.items():
        df.at[row_index, field] = value

    backup_path = backup_csv(INTAKE_ITEMS_PATH)
    save_csv(df, INTAKE_ITEMS_PATH)

    updated_item = df.loc[row_index].fillna("").to_dict()

    return {
        "success": True,
        "message": "Intake item updated.",
        "item": updated_item,
        "backup_created": str(backup_path) if backup_path else None,
    }

def remove_intake_item(intake_item_id: str) -> dict:
    """
    Remove one child intake item from user_intake_items.csv.

    This does not remove the parent intake entry.
    """
    intake_item_id = clean_text(intake_item_id, "intake_item_id", required=True)

    df = read_csv_for_write(INTAKE_ITEMS_PATH, INTAKE_ITEMS_COLUMNS)

    matching_rows = df.index[
        df["intake_item_id"].astype(str).str.strip() == intake_item_id
    ].tolist()

    if not matching_rows:
        raise ValueError(f"No intake item found with intake_item_id: {intake_item_id}")

    row_index = matching_rows[0]
    removed_item = df.loc[row_index].fillna("").to_dict()

    updated_df = df.drop(index=row_index).reset_index(drop=True)

    backup_path = backup_csv(INTAKE_ITEMS_PATH)
    save_csv(updated_df, INTAKE_ITEMS_PATH)

    return {
        "success": True,
        "message": "Intake item removed.",
        "removed_item": removed_item,
        "backup_created": str(backup_path) if backup_path else None,
    }


def remove_intake_entry(intake_id: str) -> dict:
    """
    Remove a parent intake entry from user_intake_history.csv.

    Version 1.2 uses conservative relationship protection:
    parent entries cannot be removed while child intake items still exist.
    Remove child items first with remove_intake_item().
    """
    intake_id = clean_text(intake_id, "intake_id", required=True)

    history_df = read_csv_for_write(INTAKE_HISTORY_PATH, INTAKE_HISTORY_COLUMNS)

    matching_rows = history_df.index[
        history_df["intake_id"].astype(str).str.strip() == intake_id
    ].tolist()

    if not matching_rows:
        raise ValueError(f"No intake entry found with intake_id: {intake_id}")

    child_items = get_intake_items_for_entry(intake_id)

    if child_items:
        raise ValueError(
            f"Cannot remove intake entry {intake_id} because it has "
            f"{len(child_items)} child intake item(s). Remove child items first."
        )

    row_index = matching_rows[0]
    removed_entry = history_df.loc[row_index].fillna("").to_dict()

    updated_history_df = history_df.drop(index=row_index).reset_index(drop=True)

    backup_path = backup_csv(INTAKE_HISTORY_PATH)
    save_csv(updated_history_df, INTAKE_HISTORY_PATH)

    return {
        "success": True,
        "message": "Intake entry removed.",
        "removed_entry": removed_entry,
        "child_item_count": 0,
        "backup_created": str(backup_path) if backup_path else None,
    }


def find_possible_inventory_duplicates(
    df: pd.DataFrame,
    food_item: str,
    brand: str = "",
    category: str = "",
    location: str = "",
    unit: str = "",
    expiry_date: str = "",
) -> list[dict]:
    """
    Find likely duplicate inventory rows.

    This intentionally returns warnings instead of blocking duplicates because
    duplicate-looking rows may be legitimate separate packages or batches.
    """
    if df.empty or "food_item" not in df.columns:
        return []

    food_item = clean_lower_text(food_item, "food_item", required=True)
    brand = clean_lower_text(brand, "brand")
    category = clean_lower_text(category, "category")
    location = clean_lower_text(location, "location")
    unit = clean_lower_text(unit, "unit")
    expiry_date = clean_text(expiry_date, "expiry_date")

    mask = _safe_text_series(df, "food_item") == food_item

    if brand and "brand" in df.columns:
        mask = mask & (_safe_text_series(df, "brand") == brand)

    if category and "category" in df.columns:
        mask = mask & (_safe_text_series(df, "category") == category)

    if location and "location" in df.columns:
        mask = mask & (_safe_text_series(df, "location") == location)

    if unit and "unit" in df.columns:
        mask = mask & (_safe_text_series(df, "unit") == unit)

    if expiry_date and "expiry_date" in df.columns:
        expiry_series = df["expiry_date"].fillna("").astype(str).str.strip()
        mask = mask & (expiry_series == expiry_date)

    return df_to_records(df[mask])

def intake_item_id_exists(intake_item_id: str) -> bool:
    """
    Return True if an intake item record exists for the supplied intake_item_id.
    """
    cleaned_id = clean_text(intake_item_id, "intake_item_id", required=True)

    items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    )

    return id_exists(items_df, "intake_item_id", cleaned_id)


def require_existing_intake_item_id(intake_item_id: str) -> str:
    """
    Validate that an intake_item_id exists in user_intake_items.csv.
    """
    items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    )

    return require_existing_id(
        df=items_df,
        id_column="intake_item_id",
        id_value=intake_item_id,
        entity_name="intake item",
    )


def get_intake_items_for_entry(intake_id: str) -> list[dict]:
    """
    Return all child intake item rows for a parent intake entry.

    This supports Version 1.2 relationship-safe editing and removal.
    """
    intake_id = require_existing_intake_id(intake_id)

    items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    )

    if items_df.empty or "intake_id" not in items_df.columns:
        return []

    matching_items = items_df[
        items_df["intake_id"].fillna("").astype(str).str.strip() == intake_id
    ].copy()

    return df_to_records(matching_items)


def intake_entry_has_items(intake_id: str) -> bool:
    """
    Return True if a parent intake entry has child item rows.
    """
    return len(get_intake_items_for_entry(intake_id)) > 0


# ---------------------------------------------------------------------
# Inventory consumption helpers
# ---------------------------------------------------------------------

def validate_consumption_amounts(
    quantity_used: float = 0,
    servings_used: float = 0,
) -> dict[str, float]:
    """
    Validate inventory consumption amounts.

    At least one consumption amount must be greater than zero. Both values are
    allowed because some inventory items track physical quantity, servings, or both.
    """
    quantity_value = validate_non_negative_number(quantity_used, "quantity_used")
    servings_value = validate_non_negative_number(servings_used, "servings_used")

    if quantity_value == 0 and servings_value == 0:
        raise ValueError(
            "At least one of quantity_used or servings_used must be greater than 0."
        )

    return {
        "quantity_used": quantity_value,
        "servings_used": servings_value,
    }


def calculate_inventory_after_consumption(
    inventory_item: dict,
    quantity_used: float = 0,
    servings_used: float = 0,
) -> dict:
    """
    Calculate the inventory row state after controlled consumption.

    This function performs no file writes. It only validates and returns the
    updated inventory item dictionary.
    """
    consumption_values = validate_consumption_amounts(
        quantity_used=quantity_used,
        servings_used=servings_used,
    )

    current_quantity = validate_non_negative_number(
        inventory_item.get("quantity", 0),
        "quantity",
    )
    current_servings = validate_non_negative_number(
        inventory_item.get("servings_remaining", 0),
        "servings_remaining",
    )

    current_status = validate_choice(
        inventory_item.get("stock_status", "in_stock") or "in_stock",
        VALID_STOCK_STATUSES,
        "stock_status",
    )

    final_quantity = current_quantity - consumption_values["quantity_used"]
    final_servings = current_servings - consumption_values["servings_used"]

    if final_quantity < 0:
        raise ValueError("quantity_used cannot exceed current quantity.")

    if final_servings < 0:
        raise ValueError("servings_used cannot exceed current servings.")

    # Avoid floating point residue such as 1.1102230246251565e-16.
    final_quantity = max(final_quantity, 0.0)
    final_servings = max(final_servings, 0.0)

    if final_quantity == 0 and final_servings == 0:
        final_status = "out"
    else:
        final_status = infer_stock_status(
            quantity=final_quantity,
            servings_remaining=final_servings,
            stock_status=current_status,
        )

    final_status = validate_choice(
        final_status,
        VALID_STOCK_STATUSES,
        "stock_status",
    )

    validate_inventory_stock_consistency(
        quantity=final_quantity,
        servings_remaining=final_servings,
        stock_status=final_status,
    )

    updated_item = dict(inventory_item)
    updated_item["quantity"] = final_quantity
    updated_item["servings_remaining"] = final_servings
    updated_item["stock_status"] = final_status

    return updated_item


def apply_inventory_consumption_to_df(
    inventory_df: pd.DataFrame,
    stock_id: str,
    quantity_used: float = 0,
    servings_used: float = 0,
) -> tuple[pd.DataFrame, dict, dict, dict[str, float]]:
    """
    Apply controlled inventory consumption to an inventory DataFrame.

    Returns:
    - updated inventory DataFrame
    - inventory item before consumption
    - inventory item after consumption
    - cleaned consumption amount values

    This function performs no file writes.
    """
    stock_id = clean_text(stock_id, "stock_id", required=True)

    if "stock_id" not in inventory_df.columns:
        raise ValueError("Cannot consume inventory because 'stock_id' column is missing.")

    matching_rows = inventory_df.index[
        inventory_df["stock_id"].fillna("").astype(str).str.strip() == stock_id
    ].tolist()

    if not matching_rows:
        raise ValueError(f"No inventory item found with stock_id: {stock_id}")

    row_index = matching_rows[0]

    consumption_values = validate_consumption_amounts(
        quantity_used=quantity_used,
        servings_used=servings_used,
    )

    inventory_before = inventory_df.loc[row_index].fillna("").to_dict()

    inventory_after = calculate_inventory_after_consumption(
        inventory_item=inventory_before,
        quantity_used=consumption_values["quantity_used"],
        servings_used=consumption_values["servings_used"],
    )

    updated_inventory_df = inventory_df.copy()

    updated_inventory_df.at[row_index, "quantity"] = inventory_after["quantity"]
    updated_inventory_df.at[row_index, "servings_remaining"] = inventory_after[
        "servings_remaining"
    ]
    updated_inventory_df.at[row_index, "stock_status"] = inventory_after["stock_status"]

    return (
        updated_inventory_df,
        inventory_before,
        inventory_after,
        consumption_values,
    )

def build_inventory_consumption_record(
    consumption_df: pd.DataFrame,
    inventory_before: dict,
    inventory_after: dict,
    quantity_used: float,
    servings_used: float,
    intake_id: str = "",
    intake_item_id: str = "",
    consumption_type: str = "consumed",
    tracking_confidence: str = "medium",
    notes: str = "",
) -> dict:
    """
    Build an inventory consumption event record.

    This function performs no file writes.
    """
    intake_id = clean_text(intake_id, "intake_id")
    intake_item_id = clean_text(intake_item_id, "intake_item_id")
    notes = clean_text(notes, "notes")

    consumption_type = validate_choice_or_blank(
        consumption_type,
        VALID_CONSUMPTION_TYPES,
        "consumption_type",
        default="consumed",
    )

    tracking_confidence = validate_choice_or_blank(
        tracking_confidence,
        VALID_TRACKING_CONFIDENCE,
        "tracking_confidence",
        default="medium",
    )

    quantity_value = validate_non_negative_number(quantity_used, "quantity_used")
    servings_value = validate_non_negative_number(servings_used, "servings_used")

    existing_ids = consumption_df["consumption_id"].dropna().astype(str).tolist()
    consumption_id = generate_next_id(
        existing_ids,
        prefix="consumption",
        width=3,
    )

    return {
        "consumption_id": consumption_id,
        "stock_id": clean_text(inventory_before.get("stock_id", ""), "stock_id", required=True),
        "intake_id": intake_id,
        "intake_item_id": intake_item_id,
        "food_item": clean_text(inventory_before.get("food_item", ""), "food_item"),
        "brand": clean_text(inventory_before.get("brand", ""), "brand"),
        "category": clean_text(inventory_before.get("category", ""), "category"),
        "location": clean_text(inventory_before.get("location", ""), "location"),
        "quantity_used": quantity_value,
        "unit": clean_text(inventory_before.get("unit", ""), "unit"),
        "servings_used": servings_value,
        "quantity_before": to_float(inventory_before.get("quantity"), 0),
        "servings_before": to_float(inventory_before.get("servings_remaining"), 0),
        "quantity_after": to_float(inventory_after.get("quantity"), 0),
        "servings_after": to_float(inventory_after.get("servings_remaining"), 0),
        "stock_status_before": clean_text(inventory_before.get("stock_status", ""), "stock_status"),
        "stock_status_after": clean_text(inventory_after.get("stock_status", ""), "stock_status"),
        "consumed_at": today_iso(),
        "consumption_type": consumption_type,
        "tracking_confidence": tracking_confidence,
        "notes": notes,
    }


def build_intake_item_from_inventory_row(
    intake_items_df: pd.DataFrame,
    intake_id: str,
    inventory_item: dict,
    amount_eaten: str = "",
    quantity_used: float = 0,
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
    Build a child intake item from an inventory row.

    This function performs no file writes. It creates the row dictionary only.
    """
    intake_id = clean_text(intake_id, "intake_id", required=True)
    amount_eaten = clean_text(amount_eaten, "amount_eaten")
    notes = clean_text(notes, "notes")

    stock_id = clean_text(
        inventory_item.get("stock_id", ""),
        "stock_id",
        required=True,
    )

    food_item = clean_text(
        inventory_item.get("food_item", ""),
        "food_item",
        required=True,
    )

    brand = clean_text(inventory_item.get("brand", ""), "brand")
    category = clean_text(inventory_item.get("category", ""), "category")
    unit = clean_text(inventory_item.get("unit", ""), "unit")

    nutrition_confidence = validate_choice_or_blank(
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

    existing_ids = intake_items_df["intake_item_id"].dropna().astype(str).tolist()
    intake_item_id = generate_next_id(
        existing_ids,
        prefix="intake_item",
        width=3,
    )

    return {
        "intake_item_id": intake_item_id,
        "intake_id": intake_id,
        "food_item": food_item,
        "brand": brand,
        "category": category,
        "source": "inventory",
        "stock_id": stock_id,
        "amount_eaten": amount_eaten,
        "quantity_used": numeric_values["quantity_used"],
        "unit": unit,
        "servings_used": numeric_values["servings_used"],
        "calories_estimate": numeric_values["calories_estimate"],
        "protein_g_estimate": numeric_values["protein_g_estimate"],
        "carbs_g_estimate": numeric_values["carbs_g_estimate"],
        "fat_g_estimate": numeric_values["fat_g_estimate"],
        "fibre_g_estimate": numeric_values["fibre_g_estimate"],
        "sugar_g_estimate": numeric_values["sugar_g_estimate"],
        "sodium_mg_estimate": numeric_values["sodium_mg_estimate"],
        "nutrition_confidence": nutrition_confidence,
        "notes": notes,
    }


def consume_inventory_item(
    stock_id: str,
    quantity_used: float = 0,
    servings_used: float = 0,
    consumption_type: str = "consumed",
    tracking_confidence: str = "medium",
    notes: str = "",
) -> dict:
    """
    Consume part or all of a tracked inventory item.

    This is the inventory-only Version 1.3 consumption workflow.

    It writes to:
    - user_inventory.csv
    - user_inventory_consumption.csv

    It does not:
    - create a parent intake entry
    - create a child intake item
    - remove the inventory row
    - create a food waste record

    Use this when inventory changed because the user consumed, finished,
    cooked with, or otherwise used a tracked item, but the usage should not
    be attached to a meal/intake record.

    If the item reaches zero quantity and zero servings, it remains in
    inventory with stock_status="out" so it can still support restock
    reminders and grocery personalization.
    """
    stock_id = clean_text(stock_id, "stock_id", required=True)
    notes = clean_text(notes, "notes")

    inventory_df = read_csv_for_write(
        INVENTORY_PATH,
        INVENTORY_COLUMNS,
    )

    consumption_df = read_csv_for_write(
        INVENTORY_CONSUMPTION_PATH,
        INVENTORY_CONSUMPTION_COLUMNS,
    )

    (
        updated_inventory_df,
        inventory_before,
        inventory_after,
        consumption_values,
    ) = apply_inventory_consumption_to_df(
        inventory_df=inventory_df,
        stock_id=stock_id,
        quantity_used=quantity_used,
        servings_used=servings_used,
    )

    consumption_record = build_inventory_consumption_record(
        consumption_df=consumption_df,
        inventory_before=inventory_before,
        inventory_after=inventory_after,
        quantity_used=consumption_values["quantity_used"],
        servings_used=consumption_values["servings_used"],
        consumption_type=consumption_type,
        tracking_confidence=tracking_confidence,
        notes=notes,
    )

    updated_consumption_df = pd.concat(
        [consumption_df, pd.DataFrame([consumption_record])],
        ignore_index=True,
    )

    backup_paths = save_related_csv_updates([
        (
            "inventory",
            INVENTORY_PATH,
            inventory_df,
            updated_inventory_df,
        ),
        (
            "inventory_consumption",
            INVENTORY_CONSUMPTION_PATH,
            consumption_df,
            updated_consumption_df,
        ),
    ])

    return {
        "success": True,
        "message": "Inventory item consumed and consumption event recorded.",
        "stock_id": stock_id,
        "quantity_used": consumption_values["quantity_used"],
        "servings_used": consumption_values["servings_used"],
        "consumption_record": consumption_record,
        "inventory_before": inventory_before,
        "inventory_after": inventory_after,
        "inventory_backup_created": backup_paths.get("inventory"),
        "inventory_consumption_backup_created": backup_paths.get("inventory_consumption"),
    }

def add_intake_item_from_inventory(
    intake_id: str,
    stock_id: str,
    amount_eaten: str = "",
    quantity_used: float = 0,
    servings_used: float = 0,
    calories_estimate: float = 0,
    protein_g_estimate: float = 0,
    carbs_g_estimate: float = 0,
    fat_g_estimate: float = 0,
    fibre_g_estimate: float = 0,
    sugar_g_estimate: float = 0,
    sodium_mg_estimate: float = 0,
    nutrition_confidence: str = "medium",
    consumption_type: str = "consumed",
    tracking_confidence: str = "medium",
    notes: str = "",
) -> dict:
    """
    Add a child intake item from a tracked inventory item and consume inventory.

    This is the linked Version 1.3 intake/inventory consumption workflow.

    It writes to:
    - user_intake_items.csv
    - user_inventory.csv
    - user_inventory_consumption.csv

    It does not:
    - create the parent intake entry
    - modify parent meal-level nutrition totals
    - remove the inventory row
    - create a food waste record

    Use this when the user ate or used a known inventory item as part of an
    existing meal or eating event.

    The created intake item copies food_item, brand, category, stock_id, and
    unit from the inventory row. The inventory consumption event records the
    before/after inventory state and links back to the created intake item.

    Use add_intake_entry first if the parent meal does not exist yet.
    Use add_intake_item for non-inventory food, takeaway, restaurant food,
    or historical estimates that should not deduct inventory.
    """
    intake_id = clean_text(intake_id, "intake_id", required=True)
    stock_id = clean_text(stock_id, "stock_id", required=True)
    amount_eaten = clean_text(amount_eaten, "amount_eaten")
    notes = clean_text(notes, "notes")

    inventory_df = read_csv_for_write(
        INVENTORY_PATH,
        INVENTORY_COLUMNS,
    )

    history_df = read_csv_for_write(
        INTAKE_HISTORY_PATH,
        INTAKE_HISTORY_COLUMNS,
    )

    intake_items_df = read_csv_for_write(
        INTAKE_ITEMS_PATH,
        INTAKE_ITEMS_COLUMNS,
    )

    consumption_df = read_csv_for_write(
        INVENTORY_CONSUMPTION_PATH,
        INVENTORY_CONSUMPTION_COLUMNS,
    )

    intake_id = require_existing_id(
        df=history_df,
        id_column="intake_id",
        id_value=intake_id,
        entity_name="intake entry",
    )

    (
        updated_inventory_df,
        inventory_before,
        inventory_after,
        consumption_values,
    ) = apply_inventory_consumption_to_df(
        inventory_df=inventory_df,
        stock_id=stock_id,
        quantity_used=quantity_used,
        servings_used=servings_used,
    )

    new_intake_item = build_intake_item_from_inventory_row(
        intake_items_df=intake_items_df,
        intake_id=intake_id,
        inventory_item=inventory_before,
        amount_eaten=amount_eaten,
        quantity_used=consumption_values["quantity_used"],
        servings_used=consumption_values["servings_used"],
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

    consumption_record = build_inventory_consumption_record(
        consumption_df=consumption_df,
        inventory_before=inventory_before,
        inventory_after=inventory_after,
        quantity_used=consumption_values["quantity_used"],
        servings_used=consumption_values["servings_used"],
        intake_id=intake_id,
        intake_item_id=new_intake_item["intake_item_id"],
        consumption_type=consumption_type,
        tracking_confidence=tracking_confidence,
        notes=notes,
    )

    updated_intake_items_df = pd.concat(
        [intake_items_df, pd.DataFrame([new_intake_item])],
        ignore_index=True,
    )

    updated_consumption_df = pd.concat(
        [consumption_df, pd.DataFrame([consumption_record])],
        ignore_index=True,
    )

    backup_paths = save_related_csv_updates([
        (
            "inventory",
            INVENTORY_PATH,
            inventory_df,
            updated_inventory_df,
        ),
        (
            "intake_items",
            INTAKE_ITEMS_PATH,
            intake_items_df,
            updated_intake_items_df,
        ),
        (
            "inventory_consumption",
            INVENTORY_CONSUMPTION_PATH,
            consumption_df,
            updated_consumption_df,
        ),
    ])

    return {
        "success": True,
        "message": (
            "Intake item added from inventory, inventory was consumed, "
            "and consumption event was recorded."
        ),
        "intake_item": new_intake_item,
        "consumption_record": consumption_record,
        "stock_id": stock_id,
        "quantity_used": consumption_values["quantity_used"],
        "servings_used": consumption_values["servings_used"],
        "inventory_before": inventory_before,
        "inventory_after": inventory_after,
        "inventory_backup_created": backup_paths.get("inventory"),
        "intake_items_backup_created": backup_paths.get("intake_items"),
        "inventory_consumption_backup_created": backup_paths.get("inventory_consumption"),
    }


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
    stock_status: str = "in_stock",
    expiry_date: str = "",
    notes: str = "",
) -> dict:
    """
    Add a new item to the active inventory CSV.

    This function cleans text fields, validates numeric/date/status fields,
    warns about possible duplicates, creates a backup, appends the new row,
    and returns the created item.
    """
    food_item = clean_text(food_item, "food_item", required=True)
    brand = clean_text(brand, "brand")
    category = clean_text(category, "category")
    location = clean_text(location, "location")
    unit = clean_text(unit, "unit")
    stock_status = clean_text(stock_status, "stock_status") or "in_stock"
    expiry_date = clean_text(expiry_date, "expiry_date")
    notes = clean_text(notes, "notes")

    validate_date_or_blank(expiry_date, "expiry_date")

    quantity_value = validate_non_negative_number(quantity, "quantity")
    servings_value = validate_non_negative_number(servings_remaining, "servings_remaining")

    stock_status = validate_choice(stock_status, VALID_STOCK_STATUSES, "stock_status")
    stock_status = infer_stock_status(quantity_value, servings_value, stock_status)
    stock_status = validate_choice(stock_status, VALID_STOCK_STATUSES, "stock_status")

    validate_inventory_stock_consistency(quantity_value, servings_value, stock_status)

    df = read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)

    possible_duplicates = find_possible_inventory_duplicates(
        df=df,
        food_item=food_item,
        brand=brand,
        category=category,
        location=location,
        unit=unit,
        expiry_date=expiry_date,
    )

    existing_ids = df["stock_id"].dropna().astype(str).tolist()
    stock_id = generate_next_id(existing_ids, prefix="inv", width=3)

    new_item = {
        "stock_id": stock_id,
        "food_item": food_item,
        "brand": brand,
        "category": category,
        "location": location,
        "quantity": quantity_value,
        "unit": unit,
        "servings_remaining": servings_value,
        "initial_quantity": quantity_value,
        "initial_servings": servings_value,
        "stock_status": stock_status,
        "expiry_date": expiry_date,
        "date_added": today_iso(),
        "notes": notes,
    }

    backup_path = backup_csv(INVENTORY_PATH)
    updated_df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
    save_csv(updated_df, INVENTORY_PATH)

    warnings = []
    if possible_duplicates:
        warnings.append(
            "Possible duplicate inventory item found. Consider using update_inventory_item() "
            "if this item already exists."
        )

    return {
        "success": True,
        "message": "Inventory item added.",
        "item": new_item,
        "backup_created": str(backup_path) if backup_path else None,
        "warnings": warnings,
        "possible_duplicates": possible_duplicates,
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
    Update an existing tracked inventory item.

    Fields left as None are not changed. String fields can be set to an empty
    string intentionally. After applying updates, final inventory stock state
    is re-validated and obvious stock_status mismatches are inferred.
    """
    stock_id = clean_text(stock_id, "stock_id", required=True)

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

    updates = {field: value for field, value in updates.items() if value is not None}

    if not updates:
        raise ValueError("At least one field must be provided to update.")

    text_fields = ["food_item", "brand", "category", "location", "unit", "expiry_date", "date_added", "notes"]
    for field in text_fields:
        if field in updates:
            updates[field] = clean_text(updates[field], field, required=(field == "food_item"))

    for numeric_field in ["quantity", "servings_remaining", "initial_quantity", "initial_servings"]:
        if numeric_field in updates:
            updates[numeric_field] = validate_non_negative_number(updates[numeric_field], numeric_field)

    if "expiry_date" in updates:
        validate_date_or_blank(updates["expiry_date"], "expiry_date")

    if "date_added" in updates:
        validate_date_or_blank(updates["date_added"], "date_added")

    if "stock_status" in updates:
        updates["stock_status"] = validate_choice(updates["stock_status"], VALID_STOCK_STATUSES, "stock_status")

    df = read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)

    matching_rows = df.index[df["stock_id"].astype(str).str.strip() == stock_id].tolist()

    if not matching_rows:
        raise ValueError(f"No inventory item found with stock_id: {stock_id}")

    row_index = matching_rows[0]

    for field, value in updates.items():
        df.at[row_index, field] = value

    final_quantity = validate_non_negative_number(df.at[row_index, "quantity"], "quantity")
    final_servings = validate_non_negative_number(df.at[row_index, "servings_remaining"], "servings_remaining")
    final_status = validate_choice(df.at[row_index, "stock_status"], VALID_STOCK_STATUSES, "stock_status")
    final_status = infer_stock_status(final_quantity, final_servings, final_status)
    final_status = validate_choice(final_status, VALID_STOCK_STATUSES, "stock_status")

    validate_inventory_stock_consistency(final_quantity, final_servings, final_status)

    df.at[row_index, "quantity"] = final_quantity
    df.at[row_index, "servings_remaining"] = final_servings
    df.at[row_index, "stock_status"] = final_status

    backup_path = backup_csv(INVENTORY_PATH)
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
    Remove an item from the tracked inventory file.

    Waste records are created only for waste-related removal types. Normal
    tracking cleanup such as used_up, duplicate_entry, incorrect_entry,
    test_entry, no_longer_tracked, or unknown does not create food waste.
    """
    stock_id = clean_text(stock_id, "stock_id", required=True)
    removal_reason = clean_text(removal_reason, "removal_reason")
    notes = clean_text(notes, "notes")

    removal_type = validate_required_choice(removal_type, VALID_REMOVAL_TYPES, "removal_type")
    tracking_confidence = validate_choice_or_blank(
        tracking_confidence,
        VALID_TRACKING_CONFIDENCE,
        "tracking_confidence",
        default="medium",
    )

    create_waste = should_create_food_waste_record(removal_type)

    inventory_df = read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)

    matching_rows = inventory_df.index[
        inventory_df["stock_id"].astype(str).str.strip() == stock_id
    ].tolist()

    if not matching_rows:
        raise ValueError(f"No inventory item found with stock_id: {stock_id}")

    row_index = matching_rows[0]
    removed_item = inventory_df.loc[row_index].fillna("").to_dict()
    updated_inventory_df = inventory_df.drop(index=row_index).reset_index(drop=True)

    waste_record = None
    updated_waste_df = None
    waste_backup_path = None

    if create_waste:
        current_quantity = validate_non_negative_number(removed_item.get("quantity", 0), "quantity")
        current_servings = validate_non_negative_number(removed_item.get("servings_remaining", 0), "servings_remaining")

        initial_quantity = to_float(removed_item.get("initial_quantity"), current_quantity)
        initial_servings = to_float(removed_item.get("initial_servings"), current_servings)

        final_quantity_wasted = (
            current_quantity if quantity_wasted is None else validate_non_negative_number(quantity_wasted, "quantity_wasted")
        )
        final_servings_wasted = (
            current_servings if servings_wasted is None else validate_non_negative_number(servings_wasted, "servings_wasted")
        )

        estimated_quantity_consumed = max(initial_quantity - final_quantity_wasted, 0)
        estimated_servings_consumed = max(initial_servings - final_servings_wasted, 0)

        waste_df = read_csv_for_write(FOOD_WASTE_PATH, FOOD_WASTE_COLUMNS)
        existing_waste_ids = waste_df["waste_id"].dropna().astype(str).tolist()
        waste_id = generate_next_id(existing_waste_ids, prefix="waste", width=3)

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
            "waste_reason": removal_reason,
            "tracking_confidence": tracking_confidence,
            "notes": notes,
        }

        updated_waste_df = pd.concat([waste_df, pd.DataFrame([waste_record])], ignore_index=True)

    inventory_backup_path = backup_csv(INVENTORY_PATH)
    if create_waste:
        waste_backup_path = backup_csv(FOOD_WASTE_PATH)

    # Inventory removal is the primary requested action. The CSV helper writes atomically.
    save_csv(updated_inventory_df, INVENTORY_PATH)

    if create_waste and updated_waste_df is not None:
        save_csv(updated_waste_df, FOOD_WASTE_PATH)

    if create_waste:
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
        "removal_type": removal_type,
        "waste_record_created": create_waste,
        "waste_record": waste_record,
        "inventory_backup_created": str(inventory_backup_path) if inventory_backup_path else None,
        "waste_backup_created": str(waste_backup_path) if waste_backup_path else None,
    }
