from datetime import date

import pytest

import grocery_assistant_mcp.core.planning_service as service
from grocery_assistant_mcp.core.planning_service import (
    build_inventory_planning_signals,
    build_planning_context,
    build_standard_planning_response,
)


def test_standard_planning_response_has_required_keys():
    response = build_standard_planning_response(
        tool_name="review_planning_context",
        summary="Planning context prepared.",
    )

    assert response["tool_name"] == "review_planning_context"
    assert response["status"] == "success"
    assert response["signals"]["inventory_signals"] == []
    assert response["recommendations"] == []
    assert response["warnings"] == []
    assert response["next_actions"] == []
    assert response["safety"]["read_only"] is True
    assert response["metadata"]["version"] == "1.5A"


def test_inventory_signals_include_available_use_soon_and_low_stock():
    records = [
        {
            "stock_id": "inv_001",
            "food_item": "Spinach",
            "category": "vegetable",
            "location": "fridge",
            "quantity": "1",
            "unit": "bag",
            "servings_remaining": "2",
            "stock_status": "low",
            "expiry_date": "2026-05-21",
        }
    ]

    result = build_inventory_planning_signals(records, today=date(2026, 5, 19))
    signal_types = {signal["signal_type"] for signal in result["inventory_signals"]}

    assert "available_inventory" in signal_types
    assert "low_stock" in signal_types
    assert "use_soon" in signal_types


def test_inventory_signals_exclude_expired_from_available():
    records = [
        {
            "stock_id": "inv_002",
            "food_item": "Yoghurt",
            "stock_status": "in_stock",
            "expiry_date": "2026-05-18",
        }
    ]

    result = build_inventory_planning_signals(records, today=date(2026, 5, 19))
    signal_types = {signal["signal_type"] for signal in result["inventory_signals"]}

    assert "expired" in signal_types
    assert "available_inventory" not in signal_types
    assert any(warning["warning_type"] == "expired_items_excluded" for warning in result["warnings"])


def test_inventory_signals_include_data_quality_for_missing_status():
    records = [
        {
            "stock_id": "inv_003",
            "food_item": "Rice",
            "stock_status": "",
            "expiry_date": "",
        }
    ]

    result = build_inventory_planning_signals(records, today=date(2026, 5, 19))
    data_quality_types = {signal["signal_type"] for signal in result["data_quality_signals"]}

    assert "missing_stock_status" in data_quality_types
    assert "no_expiry_data" in data_quality_types


def test_build_planning_context_uses_inventory_and_recent_intake(monkeypatch):
    monkeypatch.setattr(
        service,
        "list_inventory_items",
        lambda: [
            {
                "stock_id": "inv_001",
                "food_item": "Eggs",
                "stock_status": "very_low",
                "expiry_date": "2026-05-20",
                "quantity": "1",
                "unit": "carton",
            }
        ],
    )
    monkeypatch.setattr(
        service,
        "search_intake",
        lambda query="", date="": {
            "matching_entries": [
                {
                    "intake_id": "intake_001",
                    "date": "2026-05-19",
                    "meal_name": "Oats",
                    "meal_type": "breakfast",
                }
            ],
            "matching_items": [],
        },
    )

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))

    assert response["tool_name"] == "review_planning_context"
    assert response["safety"]["read_only"] is True
    assert response["metadata"]["records_checked"]["inventory"] == 1
    assert response["metadata"]["records_checked"]["intake_history"] == 1

    inventory_signal_types = {
        signal["signal_type"] for signal in response["signals"]["inventory_signals"]
    }
    intake_signal_types = {
        signal["signal_type"] for signal in response["signals"]["intake_signals"]
    }

    assert "very_low_stock" in inventory_signal_types
    assert "use_soon" in inventory_signal_types
    assert "recently_eaten" in intake_signal_types


def test_build_planning_context_returns_warning_when_no_recent_intake(monkeypatch):
    monkeypatch.setattr(service, "list_inventory_items", lambda: [])
    monkeypatch.setattr(
        service,
        "search_intake",
        lambda query="", date="": {"matching_entries": [], "matching_items": []},
    )

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))
    warning_types = {warning["warning_type"] for warning in response["warnings"]}

    assert "missing_inventory_data" in warning_types
    assert "no_recent_intake_records" in warning_types


def test_build_planning_context_does_not_mutate_inventory_csv():
    # This test is intentionally defensive. It only runs if the project exposes
    # USER_INVENTORY_CSV and the file exists in the local test environment.
    try:
        from grocery_assistant_mcp.core.grocery_service import USER_INVENTORY_CSV
    except ImportError:
        pytest.skip("USER_INVENTORY_CSV is not exposed in grocery_service")

    if not USER_INVENTORY_CSV.exists():
        pytest.skip("Inventory CSV does not exist in this test environment")

    before = USER_INVENTORY_CSV.read_text(encoding="utf-8")
    response = build_planning_context(include_inventory=True, include_recent_intake=False)
    after = USER_INVENTORY_CSV.read_text(encoding="utf-8")

    assert before == after
    assert response["safety"]["inventory_mutation_performed"] is False
