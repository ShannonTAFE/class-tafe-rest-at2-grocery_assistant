import pandas as pd

from grocery_assistant_mcp.core import grocery_service as service


def make_inventory(rows):
    return pd.DataFrame(rows)


def test_draft_restock_suggestions_empty_inventory(monkeypatch):
    monkeypatch.setattr(service, "read_inventory", lambda: pd.DataFrame())

    result = service.draft_restock_suggestions(reference_date="2026-05-19")

    assert result["status"] == "success"
    assert result["result_type"] == "restock_suggestion_draft"
    assert result["suggestions"] == []
    assert result["safety"]["read_only"] is True
    assert result["safety"]["shopping_list_mutation_performed"] is False
    assert any(
        warning["warning_type"] == "no_inventory_items"
        for warning in result["warnings"]
    )


def test_low_stock_item_becomes_restock_suggestion(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Rice",
                "category": "pantry",
                "quantity": "1",
                "servings_remaining": "1",
                "stock_status": "low",
                "expiry_date": "",
            }
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_restock_suggestions(reference_date="2026-05-19")

    assert result["suggestions"]
    rice = result["suggestions"][0]

    assert rice["item_name"] == "Rice"
    assert rice["suggestion_type"] == "restock"
    assert rice["candidate_type"] == "exact_item_restock"
    assert rice["current_status"] == "low"
    assert rice["would_create_shopping_list_record"] is False
    assert rice["requires_user_confirmation_before_write"] is True


def test_out_of_stock_item_is_restock_candidate_not_usable_ingredient(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Eggs",
                "category": "protein",
                "quantity": "0",
                "servings_remaining": "0",
                "stock_status": "out",
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

    result = service.draft_restock_suggestions(reference_date="2026-05-19")

    egg_suggestions = [
        suggestion
        for suggestion in result["suggestions"]
        if suggestion["item_name"] == "Eggs"
    ]

    assert egg_suggestions
    assert egg_suggestions[0]["current_status"] == "out"
    assert "out_of_stock" in egg_suggestions[0]["source_signal_types"]


def test_expired_item_becomes_replacement_suggestion(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Spinach",
                "category": "vegetable",
                "quantity": "1",
                "servings_remaining": "2",
                "stock_status": "in_stock",
                "expiry_date": "2026-05-15",
            }
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_restock_suggestions(reference_date="2026-05-19")

    assert result["suggestions"]
    spinach = result["suggestions"][0]

    assert spinach["item_name"] == "Spinach"
    assert spinach["candidate_type"] == "expired_replacement"
    assert spinach["current_status"] == "expired"
    assert "expired_replacement" in spinach["source_signal_types"]


def test_meal_gap_elevates_restock_priority(monkeypatch):
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
                "servings_remaining": "3",
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

    result = service.draft_restock_suggestions(reference_date="2026-05-19")

    cheese = next(
        suggestion
        for suggestion in result["suggestions"]
        if suggestion["item_name"] == "Cheese"
    )

    assert cheese["supports_meals"]
    assert cheese["priority"] in {"medium", "high"}
    assert any(
        signal["food_item"] == "Cheese"
        for signal in result["signals"]["meal_gap_signals"]
    )


def test_optional_upgrades_can_be_disabled(monkeypatch):
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
                "servings_remaining": "3",
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

    result = service.draft_restock_suggestions(
        include_low_stock=False,
        include_out_of_stock=False,
        include_expired_replacements=False,
        include_meal_gap_candidates=True,
        include_optional_upgrades=False,
        reference_date="2026-05-19",
    )

    assert all(
        suggestion["candidate_type"] != "generic_role_gap"
        for suggestion in result["suggestions"]
    )


def test_max_suggestions_is_respected(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": f"inv_{i:03}",
                "food_item": item,
                "category": "pantry",
                "quantity": "1",
                "servings_remaining": "1",
                "stock_status": "low",
                "expiry_date": "",
            }
            for i, item in enumerate(["Rice", "Pasta", "Oats", "Noodles"], start=1)
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_restock_suggestions(
        max_suggestions=2,
        reference_date="2026-05-19",
    )

    assert len(result["suggestions"]) == 2
    assert any(
        warning["warning_type"] == "max_suggestions_limited"
        for warning in result["warnings"]
    )


def test_restock_suggestions_keep_read_only_safety_contract(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Rice",
                "category": "pantry",
                "quantity": "1",
                "servings_remaining": "1",
                "stock_status": "low",
                "expiry_date": "",
            }
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_restock_suggestions(reference_date="2026-05-19")
    safety = result["safety"]

    assert safety["read_only"] is True
    assert safety["inventory_mutation_performed"] is False
    assert safety["intake_mutation_performed"] is False
    assert safety["consumption_mutation_performed"] is False
    assert safety["waste_mutation_performed"] is False
    assert safety["shopping_list_mutation_performed"] is False
    assert safety["requires_user_confirmation_before_write"] is True
