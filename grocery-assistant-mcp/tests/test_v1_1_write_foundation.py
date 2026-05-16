"""
Version 1.1 safe-write foundation tests.

Place this file in your project tests/ folder, for example:

tests/test_v1_1_write_foundation.py

These tests patch the CSV paths used by grocery_service.py so they write only
to pytest's tmp_path and do not touch your real project data.
"""

import pytest

from grocery_assistant_mcp.core import grocery_service as gs


@pytest.fixture()
def temp_grocery_csv_paths(tmp_path, monkeypatch):
    """Redirect grocery_service CSV paths to temporary test files."""
    monkeypatch.setattr(gs, "INVENTORY_PATH", tmp_path / "user_inventory.csv")
    monkeypatch.setattr(gs, "INTAKE_HISTORY_PATH", tmp_path / "user_intake_history.csv")
    monkeypatch.setattr(gs, "INTAKE_ITEMS_PATH", tmp_path / "user_intake_items.csv")
    monkeypatch.setattr(gs, "FOOD_WASTE_PATH", tmp_path / "user_food_waste.csv")
    return tmp_path


def test_add_inventory_item_creates_valid_row(temp_grocery_csv_paths):
    result = gs.add_inventory_item(
        food_item="Rolled oats",
        brand="Uncle Tobys",
        category="pantry",
        location="cupboard",
        quantity=1,
        unit="bag",
        servings_remaining=10,
        stock_status="ok",
        expiry_date="2026-12-01",
    )

    assert result["success"] is True
    assert result["item"]["stock_id"] == "inv_001"
    assert result["item"]["food_item"] == "Rolled oats"
    assert result["item"]["initial_quantity"] == 1.0
    assert result["item"]["initial_servings"] == 10.0


def test_add_inventory_item_rejects_blank_food_item(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="food_item is required"):
        gs.add_inventory_item(food_item="")


def test_add_inventory_item_rejects_negative_quantity(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="quantity must not be negative"):
        gs.add_inventory_item(food_item="Milk", quantity=-1)


def test_add_inventory_item_rejects_removed_status(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="stock_status='removed'"):
        gs.add_inventory_item(food_item="Milk", quantity=1, servings_remaining=1, stock_status="removed")


def test_update_inventory_item_updates_only_selected_fields(temp_grocery_csv_paths):
    created = gs.add_inventory_item(
        food_item="Milk",
        category="dairy",
        quantity=1,
        unit="L",
        servings_remaining=4,
    )

    stock_id = created["item"]["stock_id"]

    updated = gs.update_inventory_item(
        stock_id=stock_id,
        quantity=0.5,
        servings_remaining=2,
        stock_status="low",
    )

    assert updated["success"] is True
    assert updated["item"]["stock_id"] == stock_id
    assert updated["item"]["food_item"] == "Milk"
    assert updated["item"]["quantity"] == 0.5
    assert updated["item"]["servings_remaining"] == 2.0
    assert updated["item"]["stock_status"] == "low"


def test_update_inventory_item_rejects_unknown_stock_id(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="No inventory item found"):
        gs.update_inventory_item(stock_id="inv_999", quantity=1)


def test_update_inventory_item_infers_out_when_quantity_and_servings_are_zero(temp_grocery_csv_paths):
    created = gs.add_inventory_item(
        food_item="Milk",
        quantity=1,
        unit="L",
        servings_remaining=4,
        stock_status="ok",
    )

    stock_id = created["item"]["stock_id"]

    updated = gs.update_inventory_item(
        stock_id=stock_id,
        quantity=0,
        servings_remaining=0,
        stock_status="ok",
    )

    assert updated["item"]["stock_status"] == "out"


def test_remove_inventory_item_used_up_does_not_create_waste(temp_grocery_csv_paths):
    created = gs.add_inventory_item(
        food_item="Milk",
        quantity=1,
        unit="L",
        servings_remaining=4,
    )

    result = gs.remove_inventory_item(
        stock_id=created["item"]["stock_id"],
        removal_type="used_up",
    )

    assert result["success"] is True
    assert result["waste_record_created"] is False
    assert gs.list_inventory_items() == []
    assert gs.list_food_waste_items() == []


def test_remove_inventory_item_spoiled_creates_waste_record(temp_grocery_csv_paths):
    created = gs.add_inventory_item(
        food_item="Yogurt",
        category="dairy",
        location="fridge",
        quantity=2,
        unit="tub",
        servings_remaining=2,
        expiry_date="2026-05-20",
    )

    result = gs.remove_inventory_item(
        stock_id=created["item"]["stock_id"],
        removal_type="spoiled",
        removal_reason="Smelled bad before use",
    )

    assert result["success"] is True
    assert result["waste_record_created"] is True
    assert result["waste_record"]["waste_id"] == "waste_001"
    assert result["waste_record"]["food_item"] == "Yogurt"
    assert result["waste_record"]["waste_type"] == "spoiled"
    assert result["waste_record"]["quantity_wasted"] == 2.0
    assert result["waste_record"]["servings_wasted"] == 2.0


def test_add_intake_entry_creates_parent_meal(temp_grocery_csv_paths):
    result = gs.add_intake_entry(
        date="2026-05-16",
        time="18:30",
        meal_type="dinner",
        meal_name="Spaghetti bolognese",
        was_finished="partial",
    )

    assert result["success"] is True
    assert result["item"]["intake_id"] == "intake_001"
    assert result["item"]["meal_name"] == "Spaghetti bolognese"
    assert result["item"]["was_finished"] == "partial"


def test_add_intake_entry_rejects_invalid_date(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="date must use YYYY-MM-DD format"):
        gs.add_intake_entry(date="16/05/2026", meal_name="Toast")


def test_add_intake_entry_rejects_invalid_time(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="time must use HH:MM format"):
        gs.add_intake_entry(date="2026-05-16", time="6:30pm", meal_name="Toast")


def test_add_intake_entry_rejects_negative_nutrition(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="total_calories_estimate must not be negative"):
        gs.add_intake_entry(
            date="2026-05-16",
            meal_name="Toast",
            total_calories_estimate=-100,
        )


def test_add_intake_item_creates_child_component(temp_grocery_csv_paths):
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    item = gs.add_intake_item(
        intake_id=meal["item"]["intake_id"],
        food_item="Bread",
        servings_used=2,
        calories_estimate=180,
    )

    assert item["success"] is True
    assert item["item"]["intake_item_id"] == "intake_item_001"
    assert item["item"]["intake_id"] == meal["item"]["intake_id"]
    assert item["item"]["stock_id"] == ""


def test_add_intake_item_rejects_unknown_intake_id(temp_grocery_csv_paths):
    with pytest.raises(ValueError, match="No intake entry found"):
        gs.add_intake_item(intake_id="intake_999", food_item="Bread")


def test_add_intake_item_accepts_valid_stock_id(temp_grocery_csv_paths):
    stock = gs.add_inventory_item(food_item="Bread", quantity=1, servings_remaining=10)
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    item = gs.add_intake_item(
        intake_id=meal["item"]["intake_id"],
        food_item="Bread",
        stock_id=stock["item"]["stock_id"],
    )

    assert item["item"]["stock_id"] == stock["item"]["stock_id"]


def test_add_intake_item_rejects_unknown_stock_id_when_supplied(temp_grocery_csv_paths):
    meal = gs.add_intake_entry(date="2026-05-16", meal_name="Toast")

    with pytest.raises(ValueError, match="No inventory item found"):
        gs.add_intake_item(
            intake_id=meal["item"]["intake_id"],
            food_item="Butter",
            stock_id="inv_999",
        )
