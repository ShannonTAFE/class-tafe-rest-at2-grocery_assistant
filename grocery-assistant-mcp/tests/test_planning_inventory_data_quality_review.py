from __future__ import annotations

from grocery_assistant_mcp.core import planning_service


def _sample_planning_context() -> dict:
    return {
        "tool_name": "review_planning_context",
        "summary": "Planning context prepared with 4 signal(s). No records were changed.",
        "result_type": "planning_context",
        "status": "success",
        "inputs": {
            "recent_days": 1,
            "include_inventory": True,
            "include_recent_intake": False,
            "include_consumption": False,
            "include_waste": False,
        },
        "signals": {
            "inventory_signals": [
                {
                    "signal_id": "sig_inventory_001_available_inventory",
                    "domain": "inventory",
                    "signal_type": "available_inventory",
                    "subject": {"stock_id": "inv_001", "food_item": "Spaghetti"},
                    "severity": "low",
                    "polarity": "positive",
                    "confidence": "high",
                    "reason": "Item appears usable.",
                    "evidence": {"source": "user_inventory.csv"},
                    "data_quality": {"quality_level": "complete"},
                    "agent_guidance": "Can support soft meal-planning suggestions.",
                    "limitations": [],
                }
            ],
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": [
                {
                    "signal_id": "sig_data_quality_002_missing_quantity",
                    "domain": "data_quality",
                    "signal_type": "missing_quantity",
                    "subject": {"stock_id": "inv_002", "food_item": "Rice"},
                    "severity": "low",
                    "polarity": "caution",
                    "confidence": "high",
                    "reason": "Both quantity and servings_remaining are blank or unavailable.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["quantity", "servings_remaining"],
                        "source_values": {"quantity": "", "servings_remaining": ""},
                    },
                    "data_quality": {
                        "quality_level": "partial",
                        "missing_fields": ["quantity", "servings_remaining"],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Avoid making precise portion or serving claims.",
                    "limitations": ["Do not calculate exact meals remaining from this item."],
                },
                {
                    "signal_id": "sig_data_quality_003_no_expiry_data",
                    "domain": "data_quality",
                    "signal_type": "no_expiry_data",
                    "subject": {"stock_id": "inv_003", "food_item": "Oats"},
                    "severity": "low",
                    "polarity": "neutral",
                    "confidence": "high",
                    "reason": "No expiry date is available for this item.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["expiry_date"],
                        "source_values": {"expiry_date": ""},
                    },
                    "data_quality": {
                        "quality_level": "partial",
                        "missing_fields": ["expiry_date"],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Avoid expiry-based prioritisation for this item.",
                    "limitations": ["Cannot determine use-soon or expired status from date."],
                },
                {
                    "signal_id": "sig_data_quality_004_unrelated",
                    "domain": "data_quality",
                    "signal_type": "future_unrelated_quality_signal",
                    "subject": {"stock_id": "inv_004", "food_item": "Future item"},
                    "severity": "low",
                    "polarity": "neutral",
                    "confidence": "low",
                    "reason": "Future placeholder signal.",
                    "evidence": {"source": "user_inventory.csv"},
                    "data_quality": {"quality_level": "partial"},
                    "agent_guidance": "Placeholder.",
                    "limitations": [],
                },
            ],
            "system_signals": [],
        },
        "recommendations": [],
        "warnings": [],
        "next_actions": [],
        "safety": {
            "read_only": True,
            "inventory_mutation_performed": False,
            "intake_mutation_performed": False,
            "consumption_mutation_performed": False,
            "waste_mutation_performed": False,
            "shopping_list_mutation_performed": False,
            "requires_user_confirmation_before_write": True,
        },
        "metadata": {
            "generated_at": "2026-05-19T00:00:00+00:00",
            "version": "1.5A",
            "records_checked": {
                "inventory": 4,
                "intake_history": 0,
                "intake_items": 0,
                "consumption": 0,
                "waste": 0,
            },
            "reference_date": "2026-05-19",
        },
    }


def test_review_inventory_data_quality_returns_focused_contract(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_inventory_data_quality()

    assert result["tool_name"] == "review_inventory_data_quality"
    assert result["result_type"] == "inventory_data_quality_review"
    assert result["status"] == "success"
    assert result["metadata"]["version"] == "1.5B"
    assert result["metadata"]["source_tool"] == "review_planning_context"
    assert result["metadata"]["records_checked"]["inventory"] == 4


def test_review_inventory_data_quality_filters_selected_quality_signals(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_inventory_data_quality()

    signal_types = {
        signal["signal_type"]
        for signal in result["signals"]["data_quality_signals"]
    }

    assert signal_types == {"missing_quantity", "no_expiry_data"}
    assert "future_unrelated_quality_signal" not in signal_types
    assert result["signals"]["inventory_signals"] == []
    assert result["signals"]["intake_signals"] == []


def test_review_inventory_data_quality_respects_include_flags(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_inventory_data_quality(
        include_missing_stock_status=False,
        include_missing_quantity=False,
        include_no_expiry_data=True,
        include_invalid_expiry_date=False,
    )

    signal_types = [
        signal["signal_type"]
        for signal in result["signals"]["data_quality_signals"]
    ]

    assert signal_types == ["no_expiry_data"]
    assert result["inputs"]["include_missing_quantity"] is False
    assert result["metadata"]["filtered_data_quality_signal_types"] == [
        "no_expiry_data"
    ]


def test_review_inventory_data_quality_keeps_recommendations_empty_for_v1_5b_c(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_inventory_data_quality()

    assert result["recommendations"] == []


def test_review_inventory_data_quality_keeps_read_only_safety_contract(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_inventory_data_quality()

    safety = result["safety"]

    assert safety["read_only"] is True
    assert safety["inventory_mutation_performed"] is False
    assert safety["intake_mutation_performed"] is False
    assert safety["consumption_mutation_performed"] is False
    assert safety["waste_mutation_performed"] is False
    assert safety["shopping_list_mutation_performed"] is False
    assert safety["requires_user_confirmation_before_write"] is True


def test_review_inventory_data_quality_write_next_actions_require_confirmation(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_inventory_data_quality()

    mutation_actions = [
        action
        for action in result["next_actions"]
        if action.get("tool_name") == "update_inventory_item"
    ]

    assert mutation_actions
    assert all(action["requires_confirmation"] is True for action in mutation_actions)


def test_review_inventory_data_quality_adds_warning_when_no_selected_issues(monkeypatch):
    context = _sample_planning_context()
    context["signals"]["data_quality_signals"] = []

    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: context,
    )

    result = planning_service.review_inventory_data_quality()

    assert result["signals"]["data_quality_signals"] == []
    assert any(
        warning.get("warning_type") == "no_inventory_data_quality_issues"
        for warning in result["warnings"]
    )


def test_review_planning_context_routes_data_quality_action_to_focused_tool():
    result = planning_service.build_planning_context()

    data_quality_actions = [
        action
        for action in result["next_actions"]
        if action.get("action_type") == "review_inventory_data_quality"
    ]

    assert data_quality_actions
    assert data_quality_actions[0]["tool_name"] == "review_inventory_data_quality"
    assert data_quality_actions[0]["requires_confirmation"] is False
