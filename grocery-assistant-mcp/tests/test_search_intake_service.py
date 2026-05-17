import pandas as pd
import pytest

from grocery_assistant_mcp.core import grocery_service as service


@pytest.fixture()
def search_intake_csvs(tmp_path, monkeypatch):
    """Create isolated temporary CSV files for search_intake tests."""
    intake_history_path = tmp_path / "user_intake_history.csv"
    intake_items_path = tmp_path / "user_intake_items.csv"

    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", intake_history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", intake_items_path)

    intake_history_rows = [
        {
            "intake_id": "intake_001",
            "date": "2026-05-17",
            "time": "18:30",
            "meal_type": "dinner",
            "meal_name": "Chicken pasta",
            "meal_description": "Dinner with chicken and pasta",
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
            "notes": "Home cooked test meal",
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
        {
            "intake_id": "intake_003",
            "date": "2026-05-16",
            "time": "19:00",
            "meal_type": "dinner",
            "meal_name": "Spaghetti bolognese",
            "meal_description": "Batch cooked spaghetti meal",
            "source": "home",
            "amount_eaten": "1 large bowl",
            "portion_confidence": "medium",
            "total_calories_estimate": 760,
            "total_protein_g_estimate": 42,
            "total_carbs_g_estimate": 86,
            "total_fat_g_estimate": 25,
            "total_fibre_g_estimate": 8,
            "total_sugar_g_estimate": 10,
            "total_sodium_mg_estimate": 650,
            "nutrition_confidence": "medium",
            "was_finished": "yes",
            "leftovers_created": "yes",
            "hunger_before": "hungry",
            "hunger_after": "satisfied",
            "notes": "Batch cooked meal",
        },
        {
            "intake_id": "intake_004",
            "date": "2026-05-15",
            "time": "12:30",
            "meal_type": "lunch",
            "meal_name": "Sushi takeaway",
            "meal_description": "Takeaway lunch",
            "source": "takeaway",
            "amount_eaten": "1 pack",
            "portion_confidence": "medium",
            "total_calories_estimate": 520,
            "total_protein_g_estimate": 24,
            "total_carbs_g_estimate": 72,
            "total_fat_g_estimate": 14,
            "total_fibre_g_estimate": 4,
            "total_sugar_g_estimate": 8,
            "total_sodium_mg_estimate": 900,
            "nutrition_confidence": "low",
            "was_finished": "yes",
            "leftovers_created": "no",
            "hunger_before": "",
            "hunger_after": "",
            "notes": "Bought at work",
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
            "notes": "Used from fridge",
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
        {
            "intake_item_id": "intake_item_003",
            "intake_id": "intake_003",
            "food_item": "Beef mince",
            "brand": "Coles",
            "category": "protein",
            "source": "inventory",
            "stock_id": "inv_002",
            "amount_eaten": "150g",
            "quantity_used": 150,
            "unit": "g",
            "servings_used": 1.0,
            "calories_estimate": 320,
            "protein_g_estimate": 28,
            "carbs_g_estimate": 0,
            "fat_g_estimate": 22,
            "fibre_g_estimate": 0,
            "sugar_g_estimate": 0,
            "sodium_mg_estimate": 90,
            "nutrition_confidence": "medium",
            "notes": "Used in sauce",
        },
        {
            "intake_item_id": "intake_item_004",
            "intake_id": "intake_003",
            "food_item": "Spaghetti",
            "brand": "San Remo",
            "category": "pantry",
            "source": "home",
            "stock_id": "",
            "amount_eaten": "1.5 cups",
            "quantity_used": 1.5,
            "unit": "cups",
            "servings_used": 1.0,
            "calories_estimate": 360,
            "protein_g_estimate": 12,
            "carbs_g_estimate": 75,
            "fat_g_estimate": 2,
            "fibre_g_estimate": 5,
            "sugar_g_estimate": 3,
            "sodium_mg_estimate": 20,
            "nutrition_confidence": "medium",
            "notes": "",
        },
    ]

    pd.DataFrame(intake_history_rows, columns=service.INTAKE_HISTORY_COLUMNS).to_csv(
        intake_history_path,
        index=False,
    )
    pd.DataFrame(intake_item_rows, columns=service.INTAKE_ITEMS_COLUMNS).to_csv(
        intake_items_path,
        index=False,
    )

    return {
        "intake_history_path": intake_history_path,
        "intake_items_path": intake_items_path,
    }


def record_ids(records, field_name):
    return {str(record[field_name]) for record in records}


def get_record(records, field_name, value):
    for record in records:
        if str(record[field_name]) == value:
            return record
    raise AssertionError(f"No record found where {field_name} == {value}")


# Basic query search tests


def test_search_intake_finds_parent_entry_by_meal_name(search_intake_csvs):
    result = service.search_intake(query="spaghetti")
    assert result["success"] is True
    assert "intake_003" in record_ids(result["matching_entries"], "intake_id")
    entry = get_record(result["matching_entries"], "intake_id", "intake_003")
    assert entry["record_type"] == "intake_entry"
    assert int(entry["child_item_count"]) == 2
    assert not entry["can_remove_entry"]


def test_search_intake_finds_child_item_by_food_item(search_intake_csvs):
    result = service.search_intake(query="beef mince")
    assert result["success"] is True
    assert "intake_item_003" in record_ids(result["matching_items"], "intake_item_id")
    item = get_record(result["matching_items"], "intake_item_id", "intake_item_003")
    assert item["record_type"] == "intake_item"
    assert item["food_item"] == "Beef mince"
    assert item["parent_date"] == "2026-05-16"
    assert item["parent_meal_type"] == "dinner"
    assert item["parent_meal_name"] == "Spaghetti bolognese"
    assert "intake_003" in record_ids(result["matching_entries"], "intake_id")


def test_search_intake_is_case_insensitive(search_intake_csvs):
    result = service.search_intake(query="CHICKEN")
    assert "intake_001" in record_ids(result["matching_entries"], "intake_id")
    assert "intake_item_001" in record_ids(result["matching_items"], "intake_item_id")


def test_search_intake_returns_empty_lists_when_no_match(search_intake_csvs):
    result = service.search_intake(query="not a real meal")
    assert result["success"] is True
    assert result["entry_count"] == 0
    assert result["item_count"] == 0
    assert result["matching_entries"] == []
    assert result["matching_items"] == []


# Direct ID lookup tests


def test_search_intake_by_intake_id_returns_parent_and_children(search_intake_csvs):
    result = service.search_intake(intake_id="intake_001")
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_001"}
    assert record_ids(result["matching_items"], "intake_item_id") == {
        "intake_item_001",
        "intake_item_002",
    }
    entry = get_record(result["matching_entries"], "intake_id", "intake_001")
    assert int(entry["child_item_count"]) == 2
    assert not entry["can_remove_entry"]


def test_search_intake_by_intake_item_id_returns_child_and_parent(search_intake_csvs):
    result = service.search_intake(intake_item_id="intake_item_003")
    assert record_ids(result["matching_items"], "intake_item_id") == {"intake_item_003"}
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_003"}
    item = result["matching_items"][0]
    assert item["intake_id"] == "intake_003"
    assert item["parent_meal_name"] == "Spaghetti bolognese"


def test_search_intake_unknown_intake_id_returns_empty_results(search_intake_csvs):
    result = service.search_intake(intake_id="intake_999")
    assert result["entry_count"] == 0
    assert result["item_count"] == 0


def test_search_intake_unknown_intake_item_id_returns_empty_results(search_intake_csvs):
    result = service.search_intake(intake_item_id="intake_item_999")
    assert result["entry_count"] == 0
    assert result["item_count"] == 0


# Filter tests


def test_search_intake_filters_by_exact_date(search_intake_csvs):
    result = service.search_intake(date="2026-05-17")
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_001"}
    assert record_ids(result["matching_items"], "intake_item_id") == {
        "intake_item_001",
        "intake_item_002",
    }


def test_search_intake_filters_by_date_range(search_intake_csvs):
    result = service.search_intake(date_from="2026-05-16", date_to="2026-05-17")
    assert record_ids(result["matching_entries"], "intake_id") == {
        "intake_001",
        "intake_003",
    }
    assert record_ids(result["matching_items"], "intake_item_id") == {
        "intake_item_001",
        "intake_item_002",
        "intake_item_003",
        "intake_item_004",
    }


def test_search_intake_filters_by_meal_type(search_intake_csvs):
    result = service.search_intake(meal_type="breakfast")
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_002"}
    assert result["matching_items"] == []
    entry = result["matching_entries"][0]
    assert int(entry["child_item_count"]) == 0
    assert entry["can_remove_entry"]


def test_search_intake_filters_by_parent_source(search_intake_csvs):
    result = service.search_intake(source="takeaway")
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_004"}
    assert result["matching_items"] == []


def test_search_intake_filters_by_child_source_and_includes_parents(search_intake_csvs):
    result = service.search_intake(source="inventory")
    assert record_ids(result["matching_items"], "intake_item_id") == {
        "intake_item_001",
        "intake_item_003",
    }
    assert record_ids(result["matching_entries"], "intake_id") == {
        "intake_001",
        "intake_003",
    }


def test_search_intake_filters_by_stock_id(search_intake_csvs):
    result = service.search_intake(stock_id="inv_001")
    assert record_ids(result["matching_items"], "intake_item_id") == {"intake_item_001"}
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_001"}
    item = result["matching_items"][0]
    assert item["stock_id"] == "inv_001"
    assert item["parent_meal_name"] == "Chicken pasta"


def test_search_intake_filters_by_category(search_intake_csvs):
    result = service.search_intake(category="protein")
    assert record_ids(result["matching_items"], "intake_item_id") == {
        "intake_item_001",
        "intake_item_003",
    }
    assert record_ids(result["matching_entries"], "intake_id") == {
        "intake_001",
        "intake_003",
    }


def test_search_intake_combines_query_and_date_filter(search_intake_csvs):
    result = service.search_intake(query="chicken", date="2026-05-17")
    assert record_ids(result["matching_entries"], "intake_id") == {"intake_001"}
    assert record_ids(result["matching_items"], "intake_item_id") == {"intake_item_001"}


def test_search_intake_can_search_quantity_and_unit(search_intake_csvs):
    result = service.search_intake(query="150")
    assert "intake_item_001" in record_ids(result["matching_items"], "intake_item_id")
    assert "intake_item_003" in record_ids(result["matching_items"], "intake_item_id")

    result = service.search_intake(query="cup")
    assert "intake_item_002" in record_ids(result["matching_items"], "intake_item_id")


# Relationship context tests


def test_search_intake_parent_with_children_cannot_be_removed(search_intake_csvs):
    result = service.search_intake(intake_id="intake_001")
    entry = result["matching_entries"][0]
    assert int(entry["child_item_count"]) == 2
    assert not entry["can_remove_entry"]


def test_search_intake_parent_without_children_can_be_removed(search_intake_csvs):
    result = service.search_intake(intake_id="intake_002")
    entry = result["matching_entries"][0]
    assert int(entry["child_item_count"]) == 0
    assert entry["can_remove_entry"]


def test_search_intake_child_results_include_parent_context(search_intake_csvs):
    result = service.search_intake(intake_item_id="intake_item_001")
    item = result["matching_items"][0]
    assert item["parent_date"] == "2026-05-17"
    assert item["parent_time"] == "18:30"
    assert item["parent_meal_type"] == "dinner"
    assert item["parent_meal_name"] == "Chicken pasta"


# Limit and validation tests


def test_search_intake_applies_limit_to_entries_and_items(search_intake_csvs):
    result = service.search_intake(limit=1)
    assert result["entry_count"] == 1
    assert result["item_count"] == 1
    assert len(result["matching_entries"]) == 1
    assert len(result["matching_items"]) == 1


def test_search_intake_caps_large_limit(search_intake_csvs):
    result = service.search_intake(limit=500)
    assert result["criteria"]["limit"] == 100


def test_search_intake_rejects_zero_limit(search_intake_csvs):
    with pytest.raises(ValueError, match="limit"):
        service.search_intake(limit=0)


def test_search_intake_rejects_invalid_date(search_intake_csvs):
    with pytest.raises(ValueError, match="date"):
        service.search_intake(date="17-05-2026")


def test_search_intake_rejects_invalid_date_range_value(search_intake_csvs):
    with pytest.raises(ValueError, match="date_from"):
        service.search_intake(date_from="16-05-2026")


def test_search_intake_rejects_invalid_meal_type(search_intake_csvs):
    with pytest.raises(ValueError, match="meal_type"):
        service.search_intake(meal_type="not-a-meal")
