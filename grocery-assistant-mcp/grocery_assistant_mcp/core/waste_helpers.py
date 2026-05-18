from __future__ import annotations

import pandas as pd

from grocery_assistant_mcp.core.constants import (
    VALID_REMOVAL_TYPES,
    VALID_TRACKING_CONFIDENCE,
    WASTE_REMOVAL_TYPES,
)
from grocery_assistant_mcp.core.service_utils import (
    to_float,
    today_iso,
)
from grocery_assistant_mcp.core.write_helpers import (
    clean_text,
    generate_next_id,
    validate_choice_or_blank,
    validate_non_negative_number,
    validate_required_choice,
)


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


def build_food_waste_record(
    waste_df: pd.DataFrame,
    removed_item: dict,
    removal_type: str,
    removal_reason: str = "",
    quantity_wasted: float | None = None,
    servings_wasted: float | None = None,
    tracking_confidence: str = "medium",
    notes: str = "",
) -> dict:
    """
    Build a food waste event record from a removed inventory item.

    This function performs no file writes.
    """
    removal_type = validate_required_choice(
        removal_type,
        VALID_REMOVAL_TYPES,
        "removal_type",
    )

    tracking_confidence = validate_choice_or_blank(
        tracking_confidence,
        VALID_TRACKING_CONFIDENCE,
        "tracking_confidence",
        default="medium",
    )

    removal_reason = clean_text(removal_reason, "removal_reason")
    notes = clean_text(notes, "notes")

    current_quantity = validate_non_negative_number(
        removed_item.get("quantity", 0),
        "quantity",
    )
    current_servings = validate_non_negative_number(
        removed_item.get("servings_remaining", 0),
        "servings_remaining",
    )

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
        else validate_non_negative_number(quantity_wasted, "quantity_wasted")
    )

    final_servings_wasted = (
        current_servings
        if servings_wasted is None
        else validate_non_negative_number(servings_wasted, "servings_wasted")
    )

    estimated_quantity_consumed = max(initial_quantity - final_quantity_wasted, 0)
    estimated_servings_consumed = max(initial_servings - final_servings_wasted, 0)

    existing_waste_ids = waste_df["waste_id"].dropna().astype(str).tolist()
    waste_id = generate_next_id(existing_waste_ids, prefix="waste", width=3)

    return {
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