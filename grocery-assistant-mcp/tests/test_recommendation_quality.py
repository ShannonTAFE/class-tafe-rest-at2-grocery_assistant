import pandas as pd

from grocery_assistant_mcp.core import grocery_service as service
from grocery_assistant_mcp.core.recommendation_quality_helpers import infer_food_roles


def make_inventory(rows):
    return pd.DataFrame(rows)


def test_infer_food_roles_returns_evidence_metadata():
    result = infer_food_roles(food_item="Chicken breast", category="protein")

    assert result["roles"] == ["protein"]
    assert result["role_confidence"] == "high"
    assert "category" in result["role_sources"]
    assert "item_name" in result["role_sources"]


def test_draft_meal_suggestions_has_quality_contract(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Chicken",
                "category": "protein",
                "quantity": "1",
                "unit": "pack",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "2026-05-21",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Rice",
                "category": "pantry",
                "quantity": "1",
                "unit": "bag",
                "servings_remaining": "5",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Frozen vegetables",
                "category": "vegetable",
                "quantity": "1",
                "unit": "bag",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    assert result["status"] == "success"
    assert result["metadata"]["version"] == "1.5E"
    assert result["metadata"]["records_checked"]["inventory"] == 3
    assert result["safety"]["read_only"] is True
    assert result["safety"]["inventory_mutation_performed"] is False
    assert result["next_actions"]

    suggestion = result["suggestions"][0]
    assert "score" in suggestion
    assert "score_breakdown" in suggestion
    assert "match_quality" in suggestion
    assert "data_quality" in suggestion
    assert "assumption_level" in suggestion
    assert "recommendation_risk" in suggestion
    assert "evidence_summary" in suggestion
    assert "limitations" in suggestion
    assert "agent_guidance" in suggestion


def test_draft_meal_suggestions_empty_inventory_keeps_safety_metadata(monkeypatch):
    monkeypatch.setattr(service, "read_inventory", lambda: pd.DataFrame())

    result = service.draft_meal_suggestions(reference_date="2026-05-19")

    assert result["suggestions"] == []
    assert result["metadata"]["version"] == "1.5E"
    assert result["metadata"]["records_checked"]["inventory"] == 0
    assert result["safety"]["read_only"] is True
    assert result["next_actions"][0]["tool_name"] == "add_inventory_item"


def test_restock_suggestions_have_quality_score_breakdown(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Wraps",
                "category": "bread",
                "quantity": "1",
                "unit": "pack",
                "servings_remaining": "4",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Chicken",
                "category": "protein",
                "quantity": "1",
                "unit": "pack",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_003",
                "food_item": "Cheese",
                "category": "dairy",
                "quantity": "1",
                "unit": "block",
                "servings_remaining": "1",
                "stock_status": "low",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_restock_suggestions(reference_date="2026-05-19")

    assert result["metadata"]["version"] == "1.5E"
    assert result["safety"]["read_only"] is True

    cheese = next(
        suggestion
        for suggestion in result["suggestions"]
        if suggestion["item_name"] == "Cheese"
    )

    assert cheese["score"] >= 30
    assert cheese["priority"] in {"medium", "high"}
    assert "score_breakdown" in cheese
    assert cheese["score_breakdown"]["stock_urgency_score"] >= 20
    assert "evidence_summary" in cheese
    assert "limitations" in cheese
    assert "agent_guidance" in cheese
    assert cheese["would_create_shopping_list_record"] is False
    assert cheese["requires_user_confirmation_before_write"] is True


def test_generic_role_gap_remains_low_confidence_and_not_exact_item(monkeypatch):
    inventory = make_inventory(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Rice",
                "category": "pantry",
                "quantity": "1",
                "unit": "bag",
                "servings_remaining": "5",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Chicken",
                "category": "protein",
                "quantity": "1",
                "unit": "pack",
                "servings_remaining": "3",
                "stock_status": "in_stock",
                "expiry_date": "",
            },
        ]
    )
    monkeypatch.setattr(service, "read_inventory", lambda: inventory)

    result = service.draft_restock_suggestions(reference_date="2026-05-19")
    generic_suggestions = [
        suggestion
        for suggestion in result["suggestions"]
        if suggestion["candidate_type"] == "generic_role_gap"
    ]

    assert generic_suggestions
    generic = generic_suggestions[0]
    assert generic["confidence"] == "low"
    assert generic["source_stock_ids"] == []
    assert generic["data_quality"] == "usable_for_soft_suggestion_only"
    assert any("Do not invent" in text for text in generic["limitations"])
