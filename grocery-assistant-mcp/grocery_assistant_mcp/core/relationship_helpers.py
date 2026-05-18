from __future__ import annotations

import pandas as pd

from grocery_assistant_mcp.core.write_helpers import clean_text


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