from __future__ import annotations

import json
from datetime import date

import pandas as pd

from grocery_assistant_mcp.core.write_helpers import clean_lower_text


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
    cleaned = clean_lower_text(value, field_name)

    if cleaned not in valid_values:
        allowed = ", ".join(sorted(valid_values))
        raise ValueError(f"{field_name} must be one of: {allowed}")

    return cleaned


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


def safe_text_series(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Convert a text column into lowercase strings safely.

    This avoids errors if some values are blank or missing.
    """
    return df[column].fillna("").astype(str).str.lower()


def normalise_search_limit(
    limit: int,
    default: int = 20,
    maximum: int = 100,
) -> int:
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


def optional_clean_text(value: str | None, field_name: str) -> str:
    """
    Clean optional text search/filter values.
    """
    if value is None:
        return ""

    return str(value).strip()


def contains_query_mask(
    df: pd.DataFrame,
    columns: list[str],
    query: str,
) -> pd.Series:
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


def exact_text_mask(df: pd.DataFrame, column: str, value: str) -> pd.Series:
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