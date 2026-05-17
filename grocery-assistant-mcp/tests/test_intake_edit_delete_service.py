import pandas as pd
import pytest

from grocery_assistant_mcp.core import grocery_service as service


@pytest.fixture()
def intake_edit_delete_csvs(tmp_path, monkeypatch):
    """Create isolated temporary CSV files for intake edit/delete tests."""
    inventory_path = tmp_path / "user_inventory.csv"
    intake_history_path = tmp_path / "user_intake_history.csv"
    intake_items_path = tmp_path / "user_intake_items.csv"
    food_waste_path = tmp_path / "user_food_waste.csv"

    monkeypatch.setattr(service, "INVENTORY_PATH", inventory_path)
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", intake_history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", intake_items_path)
    monkeypatch.setattr(service, "FOOD_WASTE_PATH", food_waste_path)

    inventory_rows = [
        {
            "stock_id": "inv_001",
            "food_item": "Chicken breast",
            "brand": "Coles",
            "category": "protein",
            "location": "fridge",
            "quantity": 500,
            "unit": "g",
            "servings_remaining": 2,
            "initial_quantity": 500,
            "initial_servings": 2,
            "stock_status": "in_stock",
            "expiry_date": "2026-05-25",
            "date_added": "2026-05-17",
            "notes": "Test inventory item",
        }
    ]

    intake_history_rows = [
        {
            "intake_id": "intake_001",
            "date": "2026-05-17",
            "time": "18:30",
            "meal_type": "dinner",
            "meal_name": "Chicken pasta",
            "meal_description": "Dinner meal",
            "source": "home",
            "amount_eaten": "1 bowl",
            "portion_confidence": "medium",
            "total_calories_estimate": 700,
            "total_protein_g_estimate": 45,
            "total_carbs_g_estimate": 80,
            "total_fat_g_estimate": 20,
            "total_fibre_g_estimate": 8,
            "total_sugar_g_estimate": 6,
            "total_sodium_mg_estimate": 650,
            "nutrition_confidence": "medium",
            "was_finished": "yes",
            "leftovers_created": "no",
            "hunger_before": "hungry",
            "hunger_after": "full",
            "notes": "Original note",
        },
        {
            "intake_id": "intake_002",
            "date": "2026-05-18",
            "time": "08:00",
            "meal_type": "breakfast",
            "meal_name": "Toast",
            "meal_description": "Simple breakfast",
            "source": "home",
            "amount_eaten": "2 slices",
            "portion_confidence": "high",
            "total_calories_estimate": 300,
            "total_protein_g_estimate": 10,
            "total_carbs_g_estimate": 45,
            "total_fat_g_estimate": 8,
            "total_fibre_g_estimate": 5,
            "total_sugar_g_estimate": 4,
            "total_sodium_mg_estimate": 300,
            "nutrition_confidence": "medium",
            "was_finished": "yes",
            "leftovers_created": "no",
            "hunger_before": "",
            "hunger_after": "",
            "notes": "",
        },
    ]

    intake_item_rows = [
        {
            "intake_item_id": "intake_item_001",
            "intake_id": "intake_001",
            "food_item": "Chicken breast",
            "brand": "Coles",
            "category": "protein",
            "source": "inventory",
            "stock_id": "inv_001",
            "amount_eaten": "150g",
            "quantity_used": 150,
            "unit": "g",
            "servings_used": 1.0,
            "calories_estimate": 250,
            "protein_g_estimate": 35,
            "carbs_g_estimate": 0,
            "fat_g_estimate": 6,
            "fibre_g_estimate": 0,
            "sugar_g_estimate": 0,
            "sodium_mg_estimate": 120,
            "nutrition_confidence": "medium",
            "notes": "Original item note",
        },
        {
            "intake_item_id": "intake_item_002",
            "intake_id": "intake_001",
            "food_item": "Pasta",
            "brand": "San Remo",
            "category": "pantry",
            "source": "home",
            "stock_id": "",
            "amount_eaten": "1 cup",
            "quantity_used": 1,
            "unit": "cup",
            "servings_used": 1.0,
            "calories_estimate": 300,
            "protein_g_estimate": 10,
            "carbs_g_estimate": 60,
            "fat_g_estimate": 2,
            "fibre_g_estimate": 4,
            "sugar_g_estimate": 2,
            "sodium_mg_estimate": 20,
            "nutrition_confidence": "medium",
            "notes": "",
        },
    ]

    pd.DataFrame(inventory_rows, columns=service.INVENTORY_COLUMNS).to_csv(
        inventory_path,
        index=False,
    )
    pd.DataFrame(intake_history_rows, columns=service.INTAKE_HISTORY_COLUMNS).to_csv(
        intake_history_path,
        index=False,
    )
    pd.DataFrame(intake_item_rows, columns=service.INTAKE_ITEMS_COLUMNS).to_csv(
        intake_items_path,
        index=False,
    )
    pd.DataFrame([], columns=service.FOOD_WASTE_COLUMNS).to_csv(food_waste_path, index=False)

    return {
        "inventory_path": inventory_path,
        "intake_history_path": intake_history_path,
        "intake_items_path": intake_items_path,
        "food_waste_path": food_waste_path,
    }


def read_history(path):
    return pd.read_csv(path).fillna("")


def read_items(path):
    return pd.read_csv(path).fillna("")


# Relationship helper tests


def test_get_intake_items_for_entry_returns_child_items(intake_edit_delete_csvs):
    result = service.get_intake_items_for_entry("intake_001")
    assert len(result) == 2
    assert {item["intake_item_id"] for item in result} == {
        "intake_item_001",
        "intake_item_002",
    }


def test_intake_entry_has_items_returns_true_when_children_exist(intake_edit_delete_csvs):
    assert service.intake_entry_has_items("intake_001") is True


def test_intake_entry_has_items_returns_false_when_no_children_exist(
    intake_edit_delete_csvs,
):
    assert service.intake_entry_has_items("intake_002") is False


# update_intake_entry tests


def test_update_intake_entry_updates_only_supplied_fields(intake_edit_delete_csvs):
    result = service.update_intake_entry(
        intake_id="intake_001",
        meal_name="Updated chicken pasta",
        total_calories_estimate=650,
        notes="Updated note",
    )

    assert result["success"] is True
    assert result["item"]["meal_name"] == "Updated chicken pasta"
    assert float(result["item"]["total_calories_estimate"]) == 650
    assert result["item"]["notes"] == "Updated note"

    history_df = read_history(intake_edit_delete_csvs["intake_history_path"])
    row = history_df[history_df["intake_id"] == "intake_001"].iloc[0]
    assert row["meal_name"] == "Updated chicken pasta"
    assert float(row["total_calories_estimate"]) == 650
    assert row["meal_type"] == "dinner"
    assert row["source"] == "home"


def test_update_intake_entry_rejects_unknown_intake_id(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="No intake entry found"):
        service.update_intake_entry(intake_id="intake_999", meal_name="Should fail")


def test_update_intake_entry_requires_at_least_one_update(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="At least one field"):
        service.update_intake_entry(intake_id="intake_001")


def test_update_intake_entry_rejects_invalid_meal_type(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="meal_type"):
        service.update_intake_entry(intake_id="intake_001", meal_type="midnight feast")


def test_update_intake_entry_rejects_negative_nutrition_value(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="total_calories_estimate"):
        service.update_intake_entry(intake_id="intake_001", total_calories_estimate=-1)


def test_update_intake_entry_rejects_invalid_date(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="date"):
        service.update_intake_entry(intake_id="intake_001", date="17-05-2026")


def test_update_intake_entry_rejects_invalid_time(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="time"):
        service.update_intake_entry(intake_id="intake_001", time="6:30pm")


# update_intake_item tests


def test_update_intake_item_updates_only_supplied_fields(intake_edit_delete_csvs):
    result = service.update_intake_item(
        intake_item_id="intake_item_001",
        amount_eaten="200g",
        quantity_used=200,
        unit="g",
        servings_used=1.5,
        notes="Updated item note",
    )

    assert result["success"] is True
    assert result["item"]["amount_eaten"] == "200g"
    assert float(result["item"]["quantity_used"]) == 200
    assert result["item"]["unit"] == "g"
    assert float(result["item"]["servings_used"]) == 1.5
    assert result["item"]["notes"] == "Updated item note"

    items_df = read_items(intake_edit_delete_csvs["intake_items_path"])
    row = items_df[items_df["intake_item_id"] == "intake_item_001"].iloc[0]
    assert row["amount_eaten"] == "200g"
    assert float(row["quantity_used"]) == 200
    assert row["unit"] == "g"
    assert float(row["servings_used"]) == 1.5
    assert row["intake_id"] == "intake_001"
    assert row["stock_id"] == "inv_001"


def test_update_intake_item_can_move_item_to_existing_parent(intake_edit_delete_csvs):
    result = service.update_intake_item(
        intake_item_id="intake_item_001",
        intake_id="intake_002",
    )
    assert result["success"] is True
    assert result["item"]["intake_id"] == "intake_002"

    items_df = read_items(intake_edit_delete_csvs["intake_items_path"])
    row = items_df[items_df["intake_item_id"] == "intake_item_001"].iloc[0]
    assert row["intake_id"] == "intake_002"


def test_update_intake_item_accepts_existing_stock_id(intake_edit_delete_csvs):
    result = service.update_intake_item(
        intake_item_id="intake_item_002",
        stock_id="inv_001",
    )
    assert result["success"] is True
    assert result["item"]["stock_id"] == "inv_001"


def test_update_intake_item_rejects_unknown_intake_item_id(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="No intake item found"):
        service.update_intake_item(intake_item_id="intake_item_999", food_item="Should fail")


def test_update_intake_item_rejects_unknown_parent_intake_id(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="No intake entry found"):
        service.update_intake_item(intake_item_id="intake_item_001", intake_id="intake_999")


def test_update_intake_item_rejects_unknown_stock_id(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="No inventory item found"):
        service.update_intake_item(intake_item_id="intake_item_001", stock_id="inv_999")


def test_update_intake_item_rejects_negative_numeric_value(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="servings_used"):
        service.update_intake_item(intake_item_id="intake_item_001", servings_used=-1)


def test_update_intake_item_requires_at_least_one_update(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="At least one field"):
        service.update_intake_item(intake_item_id="intake_item_001")


# remove_intake_item tests


def test_remove_intake_item_removes_child_but_keeps_parent(intake_edit_delete_csvs):
    result = service.remove_intake_item("intake_item_001")
    assert result["success"] is True
    assert result["removed_item"]["intake_item_id"] == "intake_item_001"

    items_df = read_items(intake_edit_delete_csvs["intake_items_path"])
    history_df = read_history(intake_edit_delete_csvs["intake_history_path"])
    assert "intake_item_001" not in set(items_df["intake_item_id"])
    assert "intake_001" in set(history_df["intake_id"])


def test_remove_intake_item_rejects_unknown_item_id(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="No intake item found"):
        service.remove_intake_item("intake_item_999")


# remove_intake_entry tests


def test_remove_intake_entry_blocks_when_child_items_exist(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="child intake item"):
        service.remove_intake_entry("intake_001")


def test_remove_intake_entry_removes_parent_when_no_child_items_exist(
    intake_edit_delete_csvs,
):
    result = service.remove_intake_entry("intake_002")
    assert result["success"] is True
    assert result["removed_entry"]["intake_id"] == "intake_002"
    assert result["child_item_count"] == 0

    history_df = read_history(intake_edit_delete_csvs["intake_history_path"])
    assert "intake_002" not in set(history_df["intake_id"])
    assert "intake_001" in set(history_df["intake_id"])


def test_remove_intake_entry_rejects_unknown_intake_id(intake_edit_delete_csvs):
    with pytest.raises(ValueError, match="No intake entry found"):
        service.remove_intake_entry("intake_999")


def test_remove_intake_entry_after_removing_all_child_items(intake_edit_delete_csvs):
    service.remove_intake_item("intake_item_001")
    service.remove_intake_item("intake_item_002")
    result = service.remove_intake_entry("intake_001")

    assert result["success"] is True
    assert result["removed_entry"]["intake_id"] == "intake_001"

    history_df = read_history(intake_edit_delete_csvs["intake_history_path"])
    items_df = read_items(intake_edit_delete_csvs["intake_items_path"])
    assert "intake_001" not in set(history_df["intake_id"])
    assert items_df.empty
