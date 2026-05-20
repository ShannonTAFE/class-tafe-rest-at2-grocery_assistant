from __future__ import annotations

from grocery_assistant_mcp.core import planning_service


def _sample_planning_context() -> dict:
    return {
        "tool_name": "review_planning_context",
        "summary": "Planning context prepared with 5 signal(s). No records were changed.",
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
                    "subject": {
                        "stock_id": "inv_001",
                        "food_item": "Spaghetti",
                    },
                    "severity": "low",
                    "polarity": "positive",
                    "confidence": "high",
                    "reason": "Item appears usable.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["stock_status", "expiry_date"],
                        "source_values": {
                            "stock_status": "in_stock",
                            "expiry_date": "2026-12-01",
                        },
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Can support soft meal-planning suggestions.",
                    "limitations": [],
                    "expiry_state": "future",
                    "days_until_expiry": 196,
                },
                {
                    "signal_id": "sig_inventory_002_use_soon",
                    "domain": "inventory",
                    "signal_type": "use_soon",
                    "subject": {
                        "stock_id": "inv_002",
                        "food_item": "Spinach",
                    },
                    "severity": "medium",
                    "polarity": "caution",
                    "confidence": "high",
                    "reason": "Item is available and expires within the use-soon window.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["stock_status", "expiry_date"],
                        "source_values": {
                            "stock_status": "in_stock",
                            "expiry_date": "2026-05-21",
                        },
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Prioritise this item in meal suggestions if the user wants to reduce waste.",
                    "limitations": [
                        "Do not imply the item has already been used or consumed."
                    ],
                    "expiry_state": "use_soon",
                    "days_until_expiry": 2,
                },
                {
                    "signal_id": "sig_inventory_003_expired",
                    "domain": "inventory",
                    "signal_type": "expired",
                    "subject": {
                        "stock_id": "inv_003",
                        "food_item": "Yoghurt",
                    },
                    "severity": "critical",
                    "polarity": "negative",
                    "confidence": "high",
                    "reason": "Item is marked expired or has an expiry date in the past.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["stock_status", "expiry_date"],
                        "source_values": {
                            "stock_status": "in_stock",
                            "expiry_date": "2026-05-01",
                        },
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Exclude this item from meal suggestions unless the user confirms it is safe.",
                    "limitations": [
                        "Do not suggest consuming this item as available food."
                    ],
                    "expiry_state": "expired",
                    "days_until_expiry": -18,
                },
            ],
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": [
                {
                    "signal_id": "sig_data_quality_004_no_expiry_data",
                    "domain": "data_quality",
                    "signal_type": "no_expiry_data",
                    "subject": {
                        "stock_id": "inv_004",
                        "food_item": "Rice",
                    },
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
                    "limitations": [
                        "Cannot determine use-soon or expired status from date."
                    ],
                },
                {
                    "signal_id": "sig_data_quality_005_invalid_expiry_date",
                    "domain": "data_quality",
                    "signal_type": "invalid_expiry_date",
                    "subject": {
                        "stock_id": "inv_005",
                        "food_item": "Chicken",
                    },
                    "severity": "medium",
                    "polarity": "caution",
                    "confidence": "high",
                    "reason": "Expiry date could not be parsed.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["expiry_date"],
                        "source_values": {"expiry_date": "bad-date"},
                    },
                    "data_quality": {
                        "quality_level": "complete",
                        "missing_fields": [],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Do not make expiry-based claims for this item.",
                    "limitations": ["Expiry timing is unknown until corrected."],
                },
                {
                    "signal_id": "sig_data_quality_006_missing_quantity",
                    "domain": "data_quality",
                    "signal_type": "missing_quantity",
                    "subject": {
                        "stock_id": "inv_006",
                        "food_item": "Oats",
                    },
                    "severity": "low",
                    "polarity": "caution",
                    "confidence": "high",
                    "reason": "Quantity is missing.",
                    "evidence": {
                        "source": "user_inventory.csv",
                        "evidence_type": "observed",
                        "source_fields": ["quantity"],
                        "source_values": {"quantity": ""},
                    },
                    "data_quality": {
                        "quality_level": "partial",
                        "missing_fields": ["quantity"],
                        "conflicting_fields": [],
                        "inference_required": False,
                    },
                    "agent_guidance": "Avoid precise serving claims.",
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
                "inventory": 6,
                "intake_history": 0,
                "intake_items": 0,
                "consumption": 0,
                "waste": 0,
            },
            "reference_date": "2026-05-19",
        },
    }


def test_review_use_soon_items_returns_focused_contract(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items()

    assert result["tool_name"] == "review_use_soon_items"
    assert result["result_type"] == "inventory_use_soon_review"
    assert result["status"] == "success"
    assert result["metadata"]["version"] == "1.5B"
    assert result["metadata"]["source_tool"] == "review_planning_context"
    assert result["metadata"]["records_checked"]["inventory"] == 6
    assert result["metadata"]["selected_signal_count"] == 4


def test_review_use_soon_items_filters_expiry_related_signals(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items()

    inventory_signal_types = {
        signal["signal_type"]
        for signal in result["signals"]["inventory_signals"]
    }
    data_quality_signal_types = {
        signal["signal_type"]
        for signal in result["signals"]["data_quality_signals"]
    }

    assert inventory_signal_types == {"use_soon", "expired"}
    assert data_quality_signal_types == {"no_expiry_data", "invalid_expiry_date"}
    assert "available_inventory" not in inventory_signal_types
    assert "missing_quantity" not in data_quality_signal_types
    assert result["signals"]["intake_signals"] == []
    assert result["signals"]["consumption_signals"] == []
    assert result["signals"]["waste_signals"] == []


def test_review_use_soon_items_respects_include_flags(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items(
        include_use_soon=True,
        include_expired=False,
        include_no_expiry_data=False,
        include_invalid_expiry_date=True,
    )

    inventory_signal_types = [
        signal["signal_type"]
        for signal in result["signals"]["inventory_signals"]
    ]
    data_quality_signal_types = [
        signal["signal_type"]
        for signal in result["signals"]["data_quality_signals"]
    ]

    assert inventory_signal_types == ["use_soon"]
    assert data_quality_signal_types == ["invalid_expiry_date"]
    assert result["inputs"]["include_expired"] is False
    assert result["inputs"]["include_no_expiry_data"] is False
    assert result["metadata"]["filtered_inventory_signal_types"] == ["use_soon"]
    assert result["metadata"]["filtered_data_quality_signal_types"] == [
        "invalid_expiry_date"
    ]


def test_review_use_soon_items_keeps_recommendations_empty_for_v1_5b_b(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items()

    assert result["recommendations"] == []


def test_review_use_soon_items_keeps_read_only_safety_contract(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items()

    safety = result["safety"]

    assert safety["read_only"] is True
    assert safety["inventory_mutation_performed"] is False
    assert safety["intake_mutation_performed"] is False
    assert safety["consumption_mutation_performed"] is False
    assert safety["waste_mutation_performed"] is False
    assert safety["shopping_list_mutation_performed"] is False
    assert safety["requires_user_confirmation_before_write"] is True


def test_review_use_soon_items_write_next_actions_require_confirmation(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items()

    mutation_actions = [
        action
        for action in result["next_actions"]
        if action.get("tool_name") in {"update_inventory_item", "remove_inventory_item"}
    ]

    assert mutation_actions
    assert all(action["requires_confirmation"] is True for action in mutation_actions)


def test_review_use_soon_items_adds_warning_when_no_expiry_signals(monkeypatch):
    context = _sample_planning_context()
    context["signals"]["inventory_signals"] = [
        signal
        for signal in context["signals"]["inventory_signals"]
        if signal["signal_type"] == "available_inventory"
    ]
    context["signals"]["data_quality_signals"] = [
        signal
        for signal in context["signals"]["data_quality_signals"]
        if signal["signal_type"] == "missing_quantity"
    ]

    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: context,
    )

    result = planning_service.review_use_soon_items()

    assert result["signals"]["inventory_signals"] == []
    assert result["signals"]["data_quality_signals"] == []
    assert any(
        warning.get("warning_type") == "no_use_soon_items"
        for warning in result["warnings"]
    )


def test_review_use_soon_items_adds_warning_when_no_filters_selected(monkeypatch):
    monkeypatch.setattr(
        planning_service,
        "build_planning_context",
        lambda **_kwargs: _sample_planning_context(),
    )

    result = planning_service.review_use_soon_items(
        include_use_soon=False,
        include_expired=False,
        include_no_expiry_data=False,
        include_invalid_expiry_date=False,
    )

    assert result["signals"]["inventory_signals"] == []
    assert result["signals"]["data_quality_signals"] == []
    assert any(
        warning.get("warning_type") == "no_use_soon_filters_selected"
        for warning in result["warnings"]
    )


def test_review_planning_context_routes_use_soon_action_to_focused_tool():
    result = planning_service.build_planning_context()

    use_soon_actions = [
        action
        for action in result["next_actions"]
        if action.get("action_type") == "review_use_soon"
    ]

    assert use_soon_actions
    assert use_soon_actions[0]["tool_name"] == "review_use_soon_items"
    assert use_soon_actions[0]["requires_confirmation"] is False
