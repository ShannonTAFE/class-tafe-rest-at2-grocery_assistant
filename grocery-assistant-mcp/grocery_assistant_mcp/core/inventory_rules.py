from __future__ import annotations

import pandas as pd

from grocery_assistant_mcp.core.constants import VALID_STOCK_STATUSES
from grocery_assistant_mcp.core.service_utils import (
    df_to_records,
    safe_text_series,
    validate_choice,
)
from grocery_assistant_mcp.core.write_helpers import (
    clean_lower_text,
    clean_text,
    validate_non_negative_number,
)


def infer_stock_status(
    quantity: float,
    servings_remaining: float,
    stock_status: str,
) -> str:
    """
    Infer a safer stock_status from quantity and servings.

    Canonical statuses:
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

    mask = safe_text_series(df, "food_item") == food_item

    if brand and "brand" in df.columns:
        mask = mask & (safe_text_series(df, "brand") == brand)

    if category and "category" in df.columns:
        mask = mask & (safe_text_series(df, "category") == category)

    if location and "location" in df.columns:
        mask = mask & (safe_text_series(df, "location") == location)

    if unit and "unit" in df.columns:
        mask = mask & (safe_text_series(df, "unit") == unit)

    if expiry_date and "expiry_date" in df.columns:
        expiry_series = df["expiry_date"].fillna("").astype(str).str.strip()
        mask = mask & (expiry_series == expiry_date)

    return df_to_records(df[mask])


def validate_stock_status(stock_status: object) -> str:
    """
    Validate and return a canonical stock_status value.
    """
    return validate_choice(stock_status, VALID_STOCK_STATUSES, "stock_status")