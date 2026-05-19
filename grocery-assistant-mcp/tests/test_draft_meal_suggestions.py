import pandas as pd

from grocery_assistant_mcp.core import grocery_service as service


def make_inventory(rows):
    return pd.DataFrame(rows)


def test_draft_meal_suggestions_empty_inventory(monkeypatch):
    monkeypatch.setattr(service, "read_inventory", lambda: pd.DataFrame())

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    assert result["status"] == "success"
    assert result["result_type"] == "meal_suggestion_draft"
    assert result["suggestions"] == []
    assert any(
        warning["warning_type"] == "no_inventory_items"
        for warning in result["warnings"]
    )


def test_use_soon_item_creates_high_priority_meal_suggestion(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Chicken breast",
                "category": "protein",
                "quantity": "1",
                "servings_remaining": "2",
                "stock_status": "in_stock",
                "expiry_date": "2026-05-20",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Rice",
                "category": "pantry",
                "quantity": "1",
                "servings_remaining": "5",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Frozen vegetables",
                "category": "vegetable",
                "quantity": "1",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    assert result["suggestions"]

    top = result["suggestions"][0]

    assert top["suggestion_type"] == "use_soon_meal"
    assert top["priority"] == "high"
    assert "Chicken breast" in top["use_soon_items_used"]
    assert "Chicken breast" in top["main_items_used"]


def test_out_of_stock_item_is_not_used_as_main_ingredient(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Pasta",
                "category": "pantry",
                "quantity": "0",
                "servings_remaining": "0",
                "stock_status": "out",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Pasta sauce",
                "category": "sauce",
                "quantity": "1",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Cheese",
                "category": "dairy",
                "quantity": "1",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    all_main_items = [
        item
        for suggestion in result["suggestions"]
        for item in suggestion["main_items_used"]
    ]

    assert "Pasta" not in all_main_items


def test_low_stock_item_becomes_gap_hint_but_does_not_block_meal(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Wraps",
                "category": "bread",
                "quantity": "1",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Chicken",
                "category": "protein",
                "quantity": "1",
                "servings_remaining": "2",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Cheese",
                "category": "dairy",
                "quantity": "1",
                "servings_remaining": "1",
                "stock_status": "low",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    assert result["suggestions"]

    wrap_suggestions = [
        suggestion
        for suggestion in result["suggestions"]
        if "wrap" in suggestion["meal_name"].lower()
        or "sandwich" in suggestion["meal_name"].lower()
    ]

    assert wrap_suggestions

    suggestion = wrap_suggestions[0]

    assert suggestion["still_possible_without_missing_items"] is True
    assert "Cheese" in suggestion["main_items_used"] or "Cheese" in suggestion["missing_or_low_items"]


def test_expired_item_is_excluded_from_usable_main_items(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Spinach",
                "category": "vegetable",
                "quantity": "1",
                "servings_remaining": "2",
                "stock_status": "expired",
                "expiry_date": "2026-05-15",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Eggs",
                "category": "protein",
                "quantity": "1",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "2026-05-25",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Cheese",
                "category": "dairy",
                "quantity": "1",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    all_main_items = [
        item
        for suggestion in result["suggestions"]
        for item in suggestion["main_items_used"]
    ]

    assert "Spinach" not in all_main_items


def test_missing_expiry_data_does_not_block_meal_suggestion(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Eggs",
                "category": "protein",
                "quantity": "1",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Bread",
                "category": "bread",
                "quantity": "1",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    assert result["suggestions"]

    data_quality_signals = result["signals"]["data_quality_signals"]

    assert any(
        signal["signal_type"] == "missing_expiry_date"
        for signal in data_quality_signals
    )


def test_max_suggestions_is_respected(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Chicken",
                "category": "protein",
                "quantity": "1",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Rice",
                "category": "pantry",
                "quantity": "1",
                "servings_remaining": "5",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Pasta",
                "category": "pantry",
                "quantity": "1",
                "servings_remaining": "5",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_004",
                "food_item": "Wraps",
                "category": "bread",
                "quantity": "1",
                "servings_remaining": "5",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_005",
                "food_item": "Spinach",
                "category": "vegetable",
                "quantity": "1",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_006",
                "food_item": "Cheese",
                "category": "dairy",
                "quantity": "1",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(
        max_suggestions=2,
        reference_date="2026-05-19",
    )

    assert len(result["suggestions"]) <= 2