from __future__ import annotations

import pandas as pd

from grocery_assistant_mcp.core.constants import (
    VALID_CONFIDENCE_LEVELS,
    VALID_CONSUMPTION_TYPES,
    VALID_STOCK_STATUSES,
    VALID_TRACKING_CONFIDENCE,
)
from grocery_assistant_mcp.core.inventory_rules import (
    infer_stock_status,
    validate_inventory_stock_consistency,
)
from grocery_assistant_mcp.core.service_utils import (
    to_float,
    today_iso,
    validate_choice,
)
from grocery_assistant_mcp.core.write_helpers import (
    clean_text,
    generate_next_id,
    validate_choice_or_blank,
    validate_non_negative_fields,
    validate_non_negative_number,
)


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