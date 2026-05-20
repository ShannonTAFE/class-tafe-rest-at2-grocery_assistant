from datetime import date

import grocery_assistant_mcp.core.planning_service as service
from grocery_assistant_mcp.core.planning_service import build_planning_context


REQUIRED_TOP_LEVEL_KEYS = {
    "tool_name",
    "summary",
    "result_type",
    "status",
    "inputs",
    "signals",
    "recommendations",
    "warnings",
    "next_actions",
    "safety",
    "metadata",
}

REQUIRED_SIGNAL_GROUPS = {
    "inventory_signals",
    "intake_signals",
    "consumption_signals",
    "waste_signals",
    "data_quality_signals",
    "system_signals",
}

REQUIRED_SIGNAL_KEYS = {
    "signal_id",
    "domain",
    "signal_type",
    "subject",
    "severity",
    "polarity",
    "confidence",
    "reason",
    "evidence",
    "data_quality",
    "agent_guidance",
    "limitations",
}

REQUIRED_RECORDS_CHECKED_KEYS = {
    "inventory",
    "intake_history",
    "intake_items",
    "consumption",
    "waste",
}


def _inventory_records():
    return [
        {
            "stock_id": "inv_001",
            "food_item": "Beef mince",
            "brand": "",
            "category": "protein",
            "location": "freezer",
            "quantity": "500",
            "unit": "g",
            "servings_remaining": "2",
            "stock_status": "low",
            "expiry_date": "2026-05-25",
        },
        {
            "stock_id": "inv_002",
            "food_item": "Spinach",
            "brand": "",
            "category": "vegetable",
            "location": "fridge",
            "quantity": "1",
            "unit": "bag",
            "servings_remaining": "2",
            "stock_status": "in_stock",
            "expiry_date": "2026-05-20",
        },
        {
            "stock_id": "inv_003",
            "food_item": "Rice",
            "brand": "",
            "category": "pantry",
            "location": "cupboard",
            "quantity": "",
            "unit": "",
            "servings_remaining": "",
            "stock_status": "",
            "expiry_date": "",
        },
    ]


def _intake_result():
    return {
        "matching_entries": [
            {
                "intake_id": "intake_001",
                "date": "2026-05-19",
                "meal_name": "Oats with banana",
                "meal_type": "breakfast",
            }
        ],
        "matching_items": [
            {
                "intake_item_id": "intake_item_001",
                "intake_id": "intake_001",
                "food_item": "Oats",
            }
        ],
    }


def _patch_planning_sources(monkeypatch):
    monkeypatch.setattr(service, "list_inventory_items", lambda: _inventory_records())
    monkeypatch.setattr(service, "search_intake", lambda query="", date="": _intake_result())


def _all_signals(response):
    signals = response["signals"]
    return [
        signal
        for signal_group in signals.values()
        for signal in signal_group
    ]


def test_review_planning_context_contract_top_level_shape(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))

    assert REQUIRED_TOP_LEVEL_KEYS.issubset(response.keys())
    assert response["tool_name"] == "review_planning_context"
    assert response["result_type"] == "planning_context"
    assert response["status"] == "success"
    assert response["inputs"]["recent_days"] == 7
    assert REQUIRED_SIGNAL_GROUPS.issubset(response["signals"].keys())


def test_review_planning_context_contract_keeps_recommendations_empty_for_v1_5a(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))

    assert response["recommendations"] == []
    assert "suggested_meal" not in response
    assert "shopping_list" not in response


def test_review_planning_context_contract_safety_metadata(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))
    safety = response["safety"]

    assert safety["read_only"] is True
    assert safety["inventory_mutation_performed"] is False
    assert safety["intake_mutation_performed"] is False
    assert safety["consumption_mutation_performed"] is False
    assert safety["waste_mutation_performed"] is False
    assert safety["shopping_list_mutation_performed"] is False
    assert safety["requires_user_confirmation_before_write"] is True


def test_review_planning_context_contract_records_checked_metadata(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))
    records_checked = response["metadata"]["records_checked"]

    assert REQUIRED_RECORDS_CHECKED_KEYS.issubset(records_checked.keys())
    assert records_checked["inventory"] == 3
    assert records_checked["intake_history"] == 1
    assert records_checked["intake_items"] == 1
    assert records_checked["consumption"] == 0
    assert records_checked["waste"] == 0
    assert response["metadata"]["version"] == "1.5A"
    assert response["metadata"]["reference_date"] == "2026-05-19"


def test_review_planning_context_contract_signals_have_required_shape(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))
    all_signals = _all_signals(response)

    assert all_signals
    for signal in all_signals:
        assert REQUIRED_SIGNAL_KEYS.issubset(signal.keys())
        assert signal["signal_id"]
        assert signal["domain"] in {"inventory", "intake", "data_quality", "system"}
        assert signal["severity"] in {"none", "low", "medium", "high", "critical"}
        assert signal["confidence"] in {"low", "medium", "high"}
        assert isinstance(signal["subject"], dict)
        assert isinstance(signal["evidence"], dict)
        assert isinstance(signal["data_quality"], dict)
        assert isinstance(signal["limitations"], list)


def test_review_planning_context_contract_expected_signal_types(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))
    inventory_signal_types = {
        signal["signal_type"] for signal in response["signals"]["inventory_signals"]
    }
    intake_signal_types = {
        signal["signal_type"] for signal in response["signals"]["intake_signals"]
    }
    data_quality_signal_types = {
        signal["signal_type"] for signal in response["signals"]["data_quality_signals"]
    }

    assert "available_inventory" in inventory_signal_types
    assert "low_stock" in inventory_signal_types
    assert "use_soon" in inventory_signal_types
    assert "recently_eaten" in intake_signal_types
    assert "missing_stock_status" in data_quality_signal_types
    assert "missing_quantity" in data_quality_signal_types
    assert "no_expiry_data" in data_quality_signal_types


def test_review_planning_context_contract_next_actions_are_tool_routing_hints(monkeypatch):
    _patch_planning_sources(monkeypatch)

    response = build_planning_context(recent_days=7, today=date(2026, 5, 19))
    next_actions = response["next_actions"]

    assert next_actions
    for action in next_actions:
        assert {"action_type", "label", "tool_name", "requires_confirmation", "reason"}.issubset(
            action.keys()
        )
        assert isinstance(action["requires_confirmation"], bool)

    mutation_actions = [
        action
        for action in next_actions
        if action["tool_name"] in {"add_meal_with_inventory_items", "update_inventory_item"}
    ]
    assert mutation_actions
    assert all(action["requires_confirmation"] is True for action in mutation_actions)
