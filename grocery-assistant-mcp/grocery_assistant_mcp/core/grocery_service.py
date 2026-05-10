import json
import logging
from pathlib import Path

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


def summarise_intake_day(date: str) -> dict:
    """
    Summarise what was eaten on a specific date.

    Expected date format:
    YYYY-MM-DD
    """
    history_df = read_intake_history()
    items_df = read_intake_items()

    if history_df.empty or "date" not in history_df.columns:
        day_history = pd.DataFrame()
    else:
        day_history = history_df[history_df["date"].astype(str) == date]

    if items_df.empty or "date" not in items_df.columns:
        day_items = pd.DataFrame()
    else:
        day_items = items_df[items_df["date"].astype(str) == date]

    nutrition_columns = [
        "calories_estimate",
        "protein_g_estimate",
        "carbs_g_estimate",
        "fat_g_estimate",
        "fibre_g_estimate",
        "sugar_g_estimate",
        "sodium_mg_estimate",
    ]

    totals = {}

    for column in nutrition_columns:
        if column in day_items.columns:
            totals[column] = float(
                pd.to_numeric(day_items[column], errors="coerce")
                .fillna(0)
                .sum()
            )
        else:
            totals[column] = 0.0

    return {
        "date": date,
        "meal_count": int(len(day_history)),
        "item_count": int(len(day_items)),
        "meals": df_to_records(day_history),
        "items": df_to_records(day_items),
        "nutrition_totals": totals,
    }