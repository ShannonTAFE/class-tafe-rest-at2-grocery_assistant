import json

import pandas as pd
import pytest

from grocery_assistant_mcp.core import grocery_service

from grocery_assistant_mcp.core.grocery_service import (
    read_csv_file,
    read_inventory,
    read_food_waste,
    read_intake_history,
    read_intake_items,
    df_to_records,
    to_json,
    list_inventory_items,
    list_food_waste_items,
    find_inventory_item,
    get_daily_intake_summary,
    get_recent_intake,
    add_inventory_item,
    update_inventory_item,
    remove_inventory_item,
)


@pytest.fixture
def temp_inventory_and_waste_csv(tmp_path, monkeypatch):
    temp_inventory = tmp_path / "user_inventory.csv"
    temp_waste = tmp_path / "user_food_waste.csv"

    empty_inventory = pd.DataFrame(columns=grocery_service.INVENTORY_COLUMNS)
    empty_inventory.to_csv(temp_inventory, index=False)

    empty_waste = pd.DataFrame(columns=grocery_service.FOOD_WASTE_COLUMNS)
    empty_waste.to_csv(temp_waste, index=False)

    monkeypatch.setattr(grocery_service, "INVENTORY_PATH", temp_inventory)
    monkeypatch.setattr(grocery_service, "FOOD_WASTE_PATH", temp_waste)

    return temp_inventory, temp_waste


@pytest.fixture
def temp_inventory_csv(temp_inventory_and_waste_csv):
    """Compatibility fixture for older inventory-only write tests."""
    temp_inventory, _temp_waste = temp_inventory_and_waste_csv
    return temp_inventory


def test_read_csv_file_returns_dataframe_for_existing_file(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "food_item,category,stock_status\nRice,Grains,ok\nLentils,Legumes,low\n",
        encoding="utf-8",
    )

    df = read_csv_file(csv_path)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "food_item" in df.columns


def test_read_csv_file_returns_empty_dataframe_for_missing_file(tmp_path):
    missing_path = tmp_path / "missing.csv"

    df = read_csv_file(missing_path)

    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_read_inventory_returns_dataframe():
    df = read_inventory()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_read_intake_history_returns_dataframe():
    df = read_intake_history()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_read_intake_items_returns_dataframe():
    df = read_intake_items()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_df_to_records_converts_dataframe_to_list_of_dicts():
    df = pd.DataFrame(
        [
            {"food_item": "Rice", "category": "Grains"},
            {"food_item": "Lentils", "category": "Legumes"},
        ]
    )

    records = df_to_records(df)

    assert isinstance(records, list)
    assert len(records) == 2
    assert records[0]["food_item"] == "Rice"
    assert records[1]["category"] == "Legumes"


def test_df_to_records_returns_empty_list_for_empty_dataframe():
    df = pd.DataFrame()

    records = df_to_records(df)

    assert records == []


def test_df_to_records_replaces_nan_with_empty_string():
    df = pd.DataFrame(
        [
            {"food_item": "Rice", "notes": None},
        ]
    )

    records = df_to_records(df)

    assert records[0]["notes"] == ""


def test_to_json_returns_valid_json_string():
    data = [{"food_item": "Rice", "category": "Grains"}]

    result = to_json(data)
    parsed = json.loads(result)

    assert isinstance(result, str)
    assert parsed[0]["food_item"] == "Rice"


def test_list_inventory_items_returns_list():
    items = list_inventory_items()

    assert isinstance(items, list)


def test_list_inventory_items_can_filter_by_category():
    items = list_inventory_items(category="protein")

    assert isinstance(items, list)

    for item in items:
        assert item.get("category", "").lower() == "protein"


def test_list_inventory_items_can_filter_low_stock_only():
    items = list_inventory_items(low_stock_only=True)

    assert isinstance(items, list)

    allowed_statuses = {"low", "very low", "empty", "out"}

    for item in items:
        assert item.get("stock_status", "").lower() in allowed_statuses


def test_find_inventory_item_returns_list():
    results = find_inventory_item("rice")

    assert isinstance(results, list)


def test_find_inventory_item_results_contain_search_term_when_found():
    search_term = "rice"
    results = find_inventory_item(search_term)

    for item in results:
        searchable_text = " ".join(
            str(item.get(column, ""))
            for column in ["food_item", "brand", "category", "location", "notes"]
        ).lower()

        assert search_term in searchable_text


def test_get_daily_intake_summary_returns_expected_structure():
    summary = get_daily_intake_summary("2026-01-01")

    assert isinstance(summary, dict)
    assert "date" in summary
    assert "meal_count" in summary
    assert "item_count" in summary
    assert "meals" in summary
    assert "items" in summary
    assert "nutrition_totals" in summary


def test_get_daily_intake_summary_has_numeric_nutrition_totals():
    summary = get_daily_intake_summary("2026-01-01")

    expected_columns = {
        "calories_estimate",
        "protein_g_estimate",
        "carbs_g_estimate",
        "fat_g_estimate",
        "fibre_g_estimate",
        "sugar_g_estimate",
        "sodium_mg_estimate",
    }

    totals = summary["nutrition_totals"]

    assert set(totals.keys()) == expected_columns

    for value in totals.values():
        assert isinstance(value, float)

def test_update_inventory_item_updates_quantity(temp_inventory_csv):
    created = add_inventory_item(
        food_item="Rice",
        brand="SunRice",
        category="pantry",
        location="cupboard",
        quantity=1,
        unit="bag",
        servings_remaining=5,
        stock_status="ok",
        expiry_date="2026-12-01",
        notes="Jasmine rice",
    )

    updated = update_inventory_item(
        stock_id=created["item"]["stock_id"],
        quantity=2,
    )

    assert updated["success"] is True
    assert updated["item"]["stock_id"] == created["item"]["stock_id"]
    assert updated["item"]["food_item"] == "Rice"
    assert updated["item"]["quantity"] == 2
    assert updated["item"]["brand"] == "SunRice"
    assert updated["item"]["stock_status"] == "ok"
    
def test_update_inventory_item_updates_multiple_fields(temp_inventory_csv):
    created = add_inventory_item(
        food_item="Greek yoghurt",
        brand="Chobani",
        category="dairy",
        location="fridge",
        quantity=1,
        unit="tub",
        servings_remaining=4,
        stock_status="ok",
        expiry_date="2026-05-20",
        notes="Plain yoghurt",
    )

    updated = update_inventory_item(
        stock_id=created["item"]["stock_id"],
        quantity=2,
        servings_remaining=6,
        stock_status="low",
        notes="Bought another tub",
    )

    assert updated["success"] is True
    assert updated["item"]["stock_id"] == created["item"]["stock_id"]
    assert updated["item"]["quantity"] == 2
    assert updated["item"]["servings_remaining"] == 6
    assert updated["item"]["stock_status"] == "low"
    assert updated["item"]["notes"] == "Bought another tub"

    assert updated["item"]["food_item"] == "Greek yoghurt"
    assert updated["item"]["brand"] == "Chobani"
    assert updated["item"]["category"] == "dairy"
    assert updated["item"]["location"] == "fridge" 

def test_update_inventory_item_unknown_stock_id_raises_error(temp_inventory_csv):
    with pytest.raises(ValueError, match="No inventory item found"):
        update_inventory_item(
            stock_id="inv_missing",
            quantity=2,
        )

def test_update_inventory_item_requires_at_least_one_update_field(temp_inventory_csv):
    created = add_inventory_item(
        food_item="Milk",
        brand="Brownes",
        category="dairy",
        location="fridge",
        quantity=1,
        unit="bottle",
        servings_remaining=4,
        stock_status="ok",
        expiry_date="2026-05-18",
        notes="Full cream",
    )

    with pytest.raises(ValueError, match="At least one field"):
        update_inventory_item(
            stock_id=created["item"]["stock_id"],
        )

def test_update_inventory_item_negative_quantity_raises_error(temp_inventory_csv):
    created = add_inventory_item(
        food_item="Pasta",
        brand="San Remo",
        category="pantry",
        location="cupboard",
        quantity=1,
        unit="packet",
        servings_remaining=5,
        stock_status="ok",
        expiry_date="2026-12-01",
        notes="Spaghetti",
    )

    with pytest.raises(ValueError):
        update_inventory_item(
            stock_id=created["item"]["stock_id"],
            quantity=-1,
        )

def test_update_inventory_item_can_clear_optional_text_field(temp_inventory_csv):
    created = add_inventory_item(
        food_item="Bread",
        brand="Tip Top",
        category="bakery",
        location="pantry",
        quantity=1,
        unit="loaf",
        servings_remaining=8,
        stock_status="ok",
        expiry_date="2026-05-19",
        notes="Wholemeal",
    )

    updated = update_inventory_item(
        stock_id=created["item"]["stock_id"],
        brand="",
        notes="",
    )

    assert updated["success"] is True
    assert updated["item"]["brand"] == ""
    assert updated["item"]["notes"] == ""

def test_remove_inventory_item_used_up_creates_no_waste_record(
    temp_inventory_and_waste_csv,
):
    created = add_inventory_item(
        food_item="Rice",
        brand="SunRice",
        category="pantry",
        location="cupboard",
        quantity=1,
        unit="bag",
        servings_remaining=5,
        stock_status="ok",
        expiry_date="2026-12-01",
        notes="Jasmine rice",
    )

    result = remove_inventory_item(
        stock_id=created["item"]["stock_id"],
        removal_type="used_up",
        removal_reason="Finished normally",
    )

    assert result["success"] is True
    assert result["waste_record_created"] is False
    assert result["waste_record"] is None
    assert result["removed_item"]["food_item"] == "Rice"

    inventory_items = list_inventory_items()
    assert inventory_items == []

    waste_items = list_food_waste_items()
    assert waste_items == []

def test_remove_inventory_item_expired_creates_waste_record(
    temp_inventory_and_waste_csv,
):
    created = add_inventory_item(
        food_item="Greek yoghurt",
        brand="Chobani",
        category="dairy",
        location="fridge",
        quantity=1000,
        unit="g",
        servings_remaining=10,
        stock_status="ok",
        expiry_date="2026-05-20",
        notes="Plain yoghurt",
    )

    result = remove_inventory_item(
        stock_id=created["item"]["stock_id"],
        removal_type="expired",
        removal_reason="Expired before finishing",
        quantity_wasted=150,
        servings_wasted=1.5,
        tracking_confidence="medium",
        notes="Most of the tub was used",
    )

    assert result["success"] is True
    assert result["waste_record_created"] is True

    waste_record = result["waste_record"]

    assert waste_record["food_item"] == "Greek yoghurt"
    assert waste_record["waste_type"] == "expired"
    assert waste_record["quantity_wasted"] == 150
    assert waste_record["servings_wasted"] == 1.5
    assert waste_record["estimated_quantity_consumed"] == 850
    assert waste_record["estimated_servings_consumed"] == 8.5
    assert waste_record["tracking_confidence"] == "medium"

    inventory_items = list_inventory_items()
    assert inventory_items == []

    waste_items = list_food_waste_items()
    assert len(waste_items) == 1
    assert waste_items[0]["waste_type"] == "expired"

def test_remove_inventory_item_invalid_removal_type_raises_error(
    temp_inventory_and_waste_csv,
):
    created = add_inventory_item(
        food_item="Milk",
        brand="Brownes",
        category="dairy",
        location="fridge",
        quantity=1,
        unit="bottle",
        servings_remaining=4,
        stock_status="ok",
        expiry_date="2026-05-20",
        notes="Full cream",
    )

    with pytest.raises(ValueError, match="removal_type must be one of"):
        remove_inventory_item(
            stock_id=created["item"]["stock_id"],
            removal_type="bad_reason",
        )