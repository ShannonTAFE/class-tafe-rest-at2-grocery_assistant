import json
import logging
from pathlib import Path
from datetime import date, timedelta

import pandas as pd

from grocery_assistant_mcp.utils.paths import (
    INVENTORY_PATH,
    INTAKE_HISTORY_PATH,
    INTAKE_ITEMS_PATH,
)

logger = logging.getLogger("grocery_mcp.grocery_data")


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
    Read the inventory CSV.

    This backs the grocery://inventory MCP resource.
    """
    return read_csv_file(INVENTORY_PATH)


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
    Return inventory items.

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
        low_statuses = ["low", "very low", "empty"]
        df = df[_safe_text_series(df, "stock_status").isin(low_statuses)]

    return df_to_records(df)


def find_inventory_item(search_term: str) -> list[dict]:
    """
    Search the inventory for an item.

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
    Search the inventory by query, category, and location.

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