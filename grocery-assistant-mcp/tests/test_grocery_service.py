import json

import pandas as pd

from grocery_assistant_mcp.core.grocery_service import (
    read_csv_file,
    read_inventory,
    read_intake_history,
    read_intake_items,
    df_to_records,
    to_json,
    list_inventory_items,
    find_inventory_item,
    summarise_intake_day,
)


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

    allowed_statuses = {"low", "very low", "empty"}

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


def test_summarise_intake_day_returns_expected_structure():
    summary = summarise_intake_day("2026-01-01")

    assert isinstance(summary, dict)
    assert "date" in summary
    assert "meal_count" in summary
    assert "item_count" in summary
    assert "meals" in summary
    assert "items" in summary
    assert "nutrition_totals" in summary


def test_summarise_intake_day_has_numeric_nutrition_totals():
    summary = summarise_intake_day("2026-01-01")

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