from __future__ import annotations

from datetime import date

from grocery_assistant_mcp.core import planning_service


def _sample_planning_context() -> dict:
    return {
        "tool_name": "review_planning_context",
        "summary": "Planning context prepared with 3 signal(s). No records were changed.",
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
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["stock_status"],
                        "source_values": {"stock_status": "in_stock"},
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Can support soft meal-planning suggestions.",
                    "limitations": [],
                },
                {
                    "signal_id": "sig_inventory_002_low_stock",
                    "domain": "inventory",
                    "signal_type": "low_stock",
                    "subject": {"stock_id": "inv_002", "food_item": "Beef mince"},
                    "severity": "medium",
                    "polarity": "caution",
                    "confidence": "high",
                    "reason": "Item is marked low.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["stock_status"],
                        "source_values": {"stock_status": "low"},
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Mention as a possible restock or careful-use item.",
                    "limitations": [
                        "Do not automatically add this item to a shopping list."
                    ],
                },
                {
                    "signal_id": "sig_inventory_003_out_of_stock",
                    "domain": "inventory",
                    "signal_type": "out_of_stock",
                    "subject": {"stock_id": "inv_003", "food_item": "Eggs"},
                    "severity": "high",
                    "polarity": "negative",
                    "confidence": "high",
                    "reason": "Item is marked out of stock.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["stock_status"],
                        "source_values": {"stock_status": "out"},
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Treat as a restock candidate, not as usable inventory.",
                    "limitations": ["Do not suggest this item as currently available."],
                },
            ],
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": [],
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
                "inventory": 3,
                "intake_history": 0,
                "intake_items": 0,
                "consumption": 0,
                "waste": 0,
            },
            "reference_date": "2026-05-19",
        },
    }


def test_review_low_stock_items_returns_focused_contract(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items()

    assert result["tool_name"] == "review_low_stock_items"
    assert result["result_type"] == "inventory_low_stock_review"
    assert result["status"] == "success"
    assert result["metadata"]["version"] == "1.5B"
    assert result["metadata"]["source_tool"] == "review_planning_context"
    assert result["metadata"]["records_checked"]["inventory"] == 3


def test_review_low_stock_items_filters_only_stock_attention_signals(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items()

    signal_types = {
        signal["signal_type"]
        for signal in result["signals"]["inventory_signals"]
    }

    assert signal_types == {"low_stock", "out_of_stock"}
    assert "available_inventory" not in signal_types
    assert result["signals"]["intake_signals"] == []
    assert result["signals"]["consumption_signals"] == []
    assert result["signals"]["waste_signals"] == []


def test_review_low_stock_items_respects_include_flags(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items(
        include_low=True,
        include_very_low=True,
        include_out=False,
    )

    signal_types = [
        signal["signal_type"]
        for signal in result["signals"]["inventory_signals"]
    ]

    assert signal_types == ["low_stock"]
    assert result["inputs"]["include_out"] is False
    assert result["metadata"]["filtered_signal_types"] == [
        "low_stock",
        "very_low_stock",
    ]


def test_review_low_stock_items_keeps_recommendations_empty_for_v1_5b_a(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items()

    assert result["recommendations"] == []


def test_review_low_stock_items_keeps_read_only_safety_contract(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items()

    safety = result["safety"]

    assert safety["read_only"] is True
    assert safety["inventory_mutation_performed"] is False
    assert safety["intake_mutation_performed"] is False
    assert safety["consumption_mutation_performed"] is False
    assert safety["waste_mutation_performed"] is False
    assert safety["shopping_list_mutation_performed"] is False
    assert safety["requires_user_confirmation_before_write"] is True


def test_review_low_stock_items_write_next_actions_require_confirmation(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items()

    mutation_actions = [
        action
        for action in result["next_actions"]
        if action.get("tool_name") == "update_inventory_item"
    ]

    assert mutation_actions
    assert all(action["requires_confirmation"] is True for action in mutation_actions)


def test_review_low_stock_items_adds_warning_when_no_attention_signals(monkeypatch):
    context = _sample_planning_context()
    context["signals"]["inventory_signals"] = [
        signal
        for signal in context["signals"]["inventory_signals"]
        if signal["signal_type"] == "available_inventory"
    ]

    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: context,
    )

    result = planning_service.review_low_stock_items()

    assert result["signals"]["inventory_signals"] == []
    assert any(
        warning.get("warning_type") == "no_low_stock_items"
        for warning in result["warnings"]
    )


def test_review_low_stock_items_adds_warning_when_no_filters_selected(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_low_stock_items(
        include_low=False,
        include_very_low=False,
        include_out=False,
    )

    assert result["signals"]["inventory_signals"] == []
    assert result["metadata"]["filtered_signal_types"] == []
    assert any(
        warning.get("warning_type") == "no_low_stock_filters_selected"
        for warning in result["warnings"]
    )


def test_review_planning_context_routes_low_stock_action_to_focused_tool():
    result = planning_service.build_planning_context(today=date(2026, 5, 19))

    low_stock_actions = [
        action
        for action in result["next_actions"]
        if action.get("action_type") == "review_low_stock"
    ]

    assert low_stock_actions
    assert low_stock_actions[0]["tool_name"] == "review_low_stock_items"
    assert low_stock_actions[0]["requires_confirmation"] is False
