from __future__ import annotations

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
    VALID_CONFIDENCE_LEVELS,
    VALID_YES_NO_UNKNOWN,
    VALID_FINISHED_STATUSES,
)

from grocery_assistant_mcp.core.service_utils import (
    today_iso,
    validate_choice,
    df_to_records,
    to_json,
    safe_text_series as _safe_text_series,
    normalise_search_limit as _normalise_search_limit,
    optional_clean_text as _optional_clean_text,
    contains_query_mask as _contains_query_mask,
    exact_text_mask as _exact_text_mask,
)

from grocery_assistant_mcp.core.inventory_rules import (
    infer_stock_status,
    validate_inventory_stock_consistency,
    find_possible_inventory_duplicates,
)

from grocery_assistant_mcp.core.transaction_helpers import save_related_csv_updates

from grocery_assistant_mcp.core.relationship_helpers import (
    id_exists,
    require_existing_id,
)

from grocery_assistant_mcp.core.consumption_helpers import (
    validate_consumption_amounts,
    calculate_inventory_after_consumption,
    apply_inventory_consumption_to_df,
    build_inventory_consumption_record,
    build_intake_item_from_inventory_row,
)

from grocery_assistant_mcp.core.waste_helpers import (
    should_create_food_waste_record,
    build_food_waste_record,
)

from grocery_assistant_mcp.core.intake_helpers import (
    INTAKE_ENTRY_NUMERIC_FIELDS,
    INTAKE_ITEM_NUMERIC_FIELDS,
    clean_and_validate_intake_entry_fields,
    clean_and_validate_intake_item_fields,
    validate_intake_entry_updates,
    validate_intake_item_updates,
)

from grocery_assistant_mcp.core.batch_meal_service import add_meal_with_items

from grocery_assistant_mcp.core.batch_inventory_meal_service import (
    add_meal_with_inventory_items,
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
# Read helpers and read-only service functions
# ---------------------------------------------------------------------







def read_csv_file(path: Path) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame.

    If the file does not exist, return an empty DataFrame instead of crashing
    the MCP server.
    """
    if not path.exists():
        logger.warning("CSV file not found: %s", path)
        return pd.DataFrame()

    return pd.read_csv(path)


def read_inventory() -> pd.DataFrame:
    """
    Read user_inventory.csv as the user's tracked grocery stock state.
    """
    return read_csv_file(INVENTORY_PATH)


def read_food_waste() -> pd.DataFrame:
    """
    Read user_food_waste.csv.
    """
    return read_csv_file(FOOD_WASTE_PATH)


def read_intake_history() -> pd.DataFrame:
    """
    Read user_intake_history.csv.
    """
    return read_csv_file(INTAKE_HISTORY_PATH)


def read_intake_items() -> pd.DataFrame:
    """
    Read user_intake_items.csv.
    """
    return read_csv_file(INTAKE_ITEMS_PATH)


def read_inventory_consumption() -> pd.DataFrame:
    """
    Read user_inventory_consumption.csv.
    """
    return read_csv_file(INVENTORY_CONSUMPTION_PATH)



















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
    entry_fields = clean_and_validate_intake_entry_fields(
        date=date,
        meal_name=meal_name,
        time=time,
        meal_type=meal_type,
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

    df = read_csv_for_write(INTAKE_HISTORY_PATH, INTAKE_HISTORY_COLUMNS)

    existing_ids = df["intake_id"].dropna().astype(str).tolist()
    intake_id = generate_next_id(existing_ids, prefix="intake", width=3)

    new_entry = {
        "intake_id": intake_id,
        **entry_fields,
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

    updates = validate_intake_entry_updates(updates)

    numeric_fields = INTAKE_ENTRY_NUMERIC_FIELDS

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

    This function does not automatically deduct inventory.
    """
    intake_id = require_existing_intake_id(intake_id)

    item_fields = clean_and_validate_intake_item_fields(
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

    if item_fields["stock_id"]:
        item_fields["stock_id"] = require_existing_stock_id(item_fields["stock_id"])

    df = read_csv_for_write(INTAKE_ITEMS_PATH, INTAKE_ITEMS_COLUMNS)

    existing_ids = df["intake_item_id"].dropna().astype(str).tolist()
    intake_item_id = generate_next_id(existing_ids, prefix="intake_item", width=3)

    new_item = {
        "intake_item_id": intake_item_id,
        "intake_id": intake_id,
        **item_fields,
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

    updates = validate_intake_item_updates(updates)

    if "intake_id" in updates:
        updates["intake_id"] = require_existing_intake_id(updates["intake_id"])

    if "stock_id" in updates and updates["stock_id"]:
        updates["stock_id"] = require_existing_stock_id(updates["stock_id"])

    numeric_fields = INTAKE_ITEM_NUMERIC_FIELDS

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
        waste_df = read_csv_for_write(FOOD_WASTE_PATH, FOOD_WASTE_COLUMNS)

        waste_record = build_food_waste_record(
            waste_df=waste_df,
            removed_item=removed_item,
            removal_type=removal_type,
            removal_reason=removal_reason,
            quantity_wasted=quantity_wasted,
            servings_wasted=servings_wasted,
            tracking_confidence=tracking_confidence,
            notes=notes,
        )

        updated_waste_df = pd.concat(
            [waste_df, pd.DataFrame([waste_record])],
            ignore_index=True,
        )

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
