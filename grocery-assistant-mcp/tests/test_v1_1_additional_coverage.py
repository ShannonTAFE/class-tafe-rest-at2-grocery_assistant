"""
Additional Version 1.1 completion tests, updated for the Version 1.3 schema.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from grocery_assistant_mcp.core import grocery_service as gs


@pytest.fixture()
def temp_grocery_csv_paths(grocery_csv_paths):
    return grocery_csv_paths["INVENTORY_PATH"].parent


# ---------------------------------------------------------------------
# Inventory: search and validation
# ---------------------------------------------------------------------


def test_search_inventory_filters_by_location(temp_grocery_csv_paths):
    gs.add_inventory_item(
        food_item="Chicken breast",
        category="protein",
        location="freezer",
        quantity=500,
        unit="g",
        servings_remaining=4,
        stock_status="in_stock",
    )
    gs.add_inventory_item(
        food_item="Greek yoghurt",
        category="dairy",
        location="fridge",
        quantity=1,
        unit="tub",
        servings_remaining=5,
        stock_status="in_stock",
    )

    results = gs.search_inventory(location="freezer")

    assert len(results) == 1
    assert results[0]["food_item"] == "Chicken breast"
    assert results[0]["location"] == "freezer"


def test_add_inventory_item_rejects_negative_servings_remaining(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_inventory_item(
            food_item="Milk",
            quantity=1,
            unit="bottle",
            servings_remaining=-1,
            stock_status="in_stock",
        )


def test_add_inventory_item_rejects_invalid_expiry_date(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_inventory_item(
            food_item="Milk",
            quantity=1,
            unit="bottle",
            servings_remaining=4,
            stock_status="in_stock",
            expiry_date="16/05/2026",
        )


def test_add_inventory_item_rejects_invalid_stock_status(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_inventory_item(
            food_item="Milk",
            quantity=1,
            unit="bottle",
            servings_remaining=4,
            stock_status="available",
        )


def test_update_inventory_item_rejects_blank_stock_id(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.update_inventory_item(stock_id="", quantity=1)


def test_update_inventory_item_rejects_negative_servings_remaining(temp_grocery_csv_paths):
    created = gs.add_inventory_item(
        food_item="Rice",
        quantity=1,
        unit="bag",
        servings_remaining=5,
        stock_status="in_stock",
    )

    with pytest.raises(ValueError):
        gs.update_inventory_item(
            stock_id=created["item"]["stock_id"],
            servings_remaining=-1,
        )


def test_update_inventory_item_rejects_invalid_expiry_date(temp_grocery_csv_paths):
    created = gs.add_inventory_item(
        food_item="Rice",
        quantity=1,
        unit="bag",
        servings_remaining=5,
        stock_status="in_stock",
    )

    with pytest.raises(ValueError):
        gs.update_inventory_item(
            stock_id=created["item"]["stock_id"],
            expiry_date="31/12/2026",
        )


def test_remove_inventory_item_rejects_blank_stock_id(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.remove_inventory_item(stock_id="", removal_type="used_up")


def test_remove_inventory_item_rejects_unknown_stock_id(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.remove_inventory_item(stock_id="inv_999", removal_type="used_up")


# ---------------------------------------------------------------------
# Waste: removal type behaviour
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "removal_type",
    [
        "expired",
        "spoiled",
        "discarded",
        "unused",
        "overbought",
        "did_not_like",
    ],
)
def test_waste_removal_types_create_waste_records(temp_grocery_csv_paths, removal_type):
    created = gs.add_inventory_item(
        food_item=f"Test item {removal_type}",
        category="test",
        location="fridge",
        quantity=2,
        unit="unit",
        servings_remaining=2,
        stock_status="in_stock",
    )

    result = gs.remove_inventory_item(
        stock_id=created["item"]["stock_id"],
        removal_type=removal_type,
        removal_reason="V1.1 removal type coverage test",
    )

    assert result["success"] is True
    assert result["waste_record_created"] is True
    assert result["waste_record"] is not None
    assert result["waste_record"]["waste_type"] == removal_type
    assert gs.list_inventory_items() == []

    waste_items = gs.list_food_waste_items()
    assert len(waste_items) == 1
    assert waste_items[0]["waste_type"] == removal_type


@pytest.mark.parametrize(
    "removal_type",
    [
        "used_up",
        "duplicate_entry",
        "incorrect_entry",
        "test_entry",
        "no_longer_tracked",
        "unknown",
    ],
)
def test_non_waste_removal_types_do_not_create_waste_records(
    temp_grocery_csv_paths,
    removal_type,
):
    created = gs.add_inventory_item(
        food_item=f"Test item {removal_type}",
        category="test",
        location="pantry",
        quantity=1,
        unit="unit",
        servings_remaining=1,
        stock_status="in_stock",
    )

    result = gs.remove_inventory_item(
        stock_id=created["item"]["stock_id"],
        removal_type=removal_type,
        removal_reason="V1.1 non-waste removal type coverage test",
    )

    assert result["success"] is True
    assert result["waste_record_created"] is False
    assert result["waste_record"] is None
    assert gs.list_inventory_items() == []
    assert gs.list_food_waste_items() == []


# ---------------------------------------------------------------------
# Intake: recent intake and validation
# ---------------------------------------------------------------------


def test_get_recent_intake_returns_recent_records(temp_grocery_csv_paths):
    today = date.today().isoformat()
    old_date = (date.today() - timedelta(days=30)).isoformat()

    gs.add_intake_entry(date=today, meal_type="breakfast", meal_name="Oats")
    gs.add_intake_entry(date=old_date, meal_type="dinner", meal_name="Old dinner")

    results = gs.get_recent_intake(days_back=7)

    assert len(results) == 1
    assert results[0]["meal_name"] == "Oats"


def test_get_recent_intake_filters_by_meal_type(temp_grocery_csv_paths):
    today = date.today().isoformat()

    gs.add_intake_entry(date=today, meal_type="breakfast", meal_name="Oats")
    gs.add_intake_entry(date=today, meal_type="dinner", meal_name="Chicken rice")

    results = gs.get_recent_intake(days_back=7, meal_type="dinner")

    assert len(results) == 1
    assert results[0]["meal_type"] == "dinner"
    assert results[0]["meal_name"] == "Chicken rice"


def test_add_intake_entry_rejects_blank_date(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_intake_entry(date="", meal_name="Toast")


def test_add_intake_entry_rejects_blank_meal_name(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_intake_entry(date="2026-05-16", meal_name="")


def test_add_intake_entry_rejects_invalid_confidence_field(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_intake_entry(
            date="2026-05-16",
            meal_name="Toast",
            portion_confidence="certain",
        )


def test_add_intake_entry_rejects_invalid_status_field(temp_grocery_csv_paths):
    with pytest.raises(ValueError):
        gs.add_intake_entry(
            date="2026-05-16",
            meal_name="Toast",
            leftovers_created="sometimes",
        )


def test_add_intake_item_rejects_blank_food_item(temp_grocery_csv_paths):
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    with pytest.raises(ValueError):
        gs.add_intake_item(
            intake_id=meal["item"]["intake_id"],
            food_item="",
        )


def test_add_intake_item_rejects_negative_quantity_used(temp_grocery_csv_paths):
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    with pytest.raises(ValueError):
        gs.add_intake_item(
            intake_id=meal["item"]["intake_id"],
            food_item="Bread",
            quantity_used=-1,
        )


def test_add_intake_item_rejects_negative_servings_used(temp_grocery_csv_paths):
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    with pytest.raises(ValueError):
        gs.add_intake_item(
            intake_id=meal["item"]["intake_id"],
            food_item="Bread",
            servings_used=-1,
        )


def test_add_intake_item_rejects_negative_nutrition_value(temp_grocery_csv_paths):
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    with pytest.raises(ValueError):
        gs.add_intake_item(
            intake_id=meal["item"]["intake_id"],
            food_item="Bread",
            calories_estimate=-100,
        )


# ---------------------------------------------------------------------
# Intake: daily summary hybrid totals
# ---------------------------------------------------------------------


def test_daily_summary_uses_item_totals_and_meal_level_fallback(
    temp_grocery_csv_paths,
):
    target_date = "2026-05-16"

    meal_with_items = gs.add_intake_entry(
        date=target_date,
        meal_type="breakfast",
        meal_name="Toast with eggs",
        total_calories_estimate=999,
        total_protein_g_estimate=999,
    )

    meal_without_items = gs.add_intake_entry(
        date=target_date,
        meal_type="lunch",
        meal_name="Chicken rice",
        total_calories_estimate=500,
        total_protein_g_estimate=35,
    )

    gs.add_intake_item(
        intake_id=meal_with_items["item"]["intake_id"],
        food_item="Toast",
        calories_estimate=180,
        protein_g_estimate=6,
    )
    gs.add_intake_item(
        intake_id=meal_with_items["item"]["intake_id"],
        food_item="Eggs",
        calories_estimate=140,
        protein_g_estimate=12,
    )

    summary = gs.get_daily_intake_summary(target_date)

    assert summary["meal_count"] == 2
    assert summary["item_count"] == 2
    assert meal_with_items["item"]["intake_id"] in summary["meal_ids_using_item_totals"]
    assert meal_without_items["item"]["intake_id"] in summary["meal_ids_using_meal_totals"]
    assert summary["nutrition_totals"]["calories_estimate"] == 820.0
    assert summary["nutrition_totals"]["protein_g_estimate"] == 53.0
