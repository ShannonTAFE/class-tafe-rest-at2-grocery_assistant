"""Restock suggestion helpers for Grocery Assistant MCP Version 1.5D.

Version 1.5D is a read-only planning layer. It converts inventory state and
meal-opportunity gaps into draft restock suggestions. It must not mutate
inventory, intake, consumption, waste, or shopping-list records.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pandas as pd

from grocery_assistant_mcp.core.meal_suggestion_helpers import (
    CATEGORY_ROLE_MAP,
    MEAL_TEMPLATES,
    ROLE_KEYWORDS,
    build_meal_suggestion_draft,
)
from grocery_assistant_mcp.core.planning_helpers import (
    build_next_action,
    build_safety_metadata,
    build_warning,
    classify_expiry,
    days_until,
    normalize_stock_status,
    normalize_text,
    safe_parse_date,
)
from grocery_assistant_mcp.core.recommendation_quality_helpers import (
    RECOMMENDATION_QUALITY_VERSION,
    infer_food_roles,
    restock_quality_fields,
)

RESTOCK_VERSION = RECOMMENDATION_QUALITY_VERSION

LOW_STOCK_STATUSES = {"low", "very_low"}
OUT_OF_STOCK_STATUS = "out"
EXPIRED_STOCK_STATUS = "expired"

GAP_TYPE_WEIGHTS = {
    "low_stock_used": 10,
    "low_stock_optional": 5,
    "out_of_stock_optional": 8,
    "expired_optional": 8,
    "generic_supporting_role_gap": 6,
    "generic_optional_role_gap": 3,
}

STOCK_STATUS_WEIGHTS = {
    "expired": 35,
    "out": 40,
    "very_low": 30,
    "low": 20,
}

ROLE_LABELS = {
    "protein": "protein option",
    "base": "base ingredient",
    "bread_wrap": "bread or wrap option",
    "vegetable": "vegetable option",
    "fruit": "fruit option",
    "dairy": "dairy option",
    "sauce": "sauce or condiment option",
    "seasoning": "seasoning option",
}


CandidateMap = dict[str, dict[str, Any]]


def build_restock_suggestion_draft(
    inventory_df: pd.DataFrame,
    *,
    include_low_stock: bool = True,
    include_out_of_stock: bool = True,
    include_expired_replacements: bool = True,
    include_meal_gap_candidates: bool = True,
    include_optional_upgrades: bool = True,
    max_suggestions: int = 8,
    max_meal_suggestions: int = 5,
    use_soon_days: int = 3,
    reference_date: str = "",
) -> dict[str, Any]:
    """Build read-only restock suggestion drafts.

    The goal is to rank restock candidates using both inventory urgency and
    meal usefulness. This function does not create shopping-list rows and does
    not update any source CSV records.
    """
    inputs = {
        "include_low_stock": include_low_stock,
        "include_out_of_stock": include_out_of_stock,
        "include_expired_replacements": include_expired_replacements,
        "include_meal_gap_candidates": include_meal_gap_candidates,
        "include_optional_upgrades": include_optional_upgrades,
        "max_suggestions": max_suggestions,
        "max_meal_suggestions": max_meal_suggestions,
        "use_soon_days": use_soon_days,
        "reference_date": reference_date,
    }

    warnings: list[dict[str, Any]] = []

    if max_suggestions < 1:
        max_suggestions = 1
        inputs["max_suggestions"] = max_suggestions
        warnings.append(
            build_warning(
                warning_type="invalid_max_suggestions",
                severity="medium",
                message="max_suggestions was less than 1 and has been adjusted to 1.",
                agent_guidance="Continue with the adjusted restock suggestion limit.",
            )
        )

    if max_meal_suggestions < 1:
        max_meal_suggestions = 1
        inputs["max_meal_suggestions"] = max_meal_suggestions
        warnings.append(
            build_warning(
                warning_type="invalid_max_meal_suggestions",
                severity="medium",
                message="max_meal_suggestions was less than 1 and has been adjusted to 1.",
                agent_guidance="Continue with the adjusted internal meal suggestion limit.",
            )
        )

    reference_day = _resolve_reference_date(reference_date)

    if inventory_df is None or inventory_df.empty:
        warnings.append(
            build_warning(
                warning_type="no_inventory_items",
                severity="low",
                message="No inventory items were available to draft restock suggestions.",
                agent_guidance="Do not invent restock suggestions. Ask the user to add inventory items first.",
            )
        )
        return _build_response(
            inputs=inputs,
            suggestions=[],
            warnings=warnings,
            records_checked=0,
            reference_day=reference_day,
            stock_attention_signals=[],
            expired_replacement_signals=[],
            meal_gap_signals=[],
            meal_support_signals=[],
            candidate_merge_signals=[],
            data_quality_signals=[],
        )

    item_signals = _build_item_restock_signals(
        inventory_df=inventory_df,
        today=reference_day,
        use_soon_days=use_soon_days,
    )

    meal_result = (
        build_meal_suggestion_draft(
            inventory_df,
            include_use_soon=True,
            include_inventory_based=True,
            include_gap_hints=True,
            max_suggestions=max_meal_suggestions,
            use_soon_days=use_soon_days,
            reference_date=reference_day.isoformat(),
        )
        if include_meal_gap_candidates or include_optional_upgrades
        else _empty_meal_result()
    )

    stock_attention_signals = _build_stock_attention_signals(
        item_signals=item_signals,
        include_low_stock=include_low_stock,
        include_out_of_stock=include_out_of_stock,
    )
    expired_replacement_signals = _build_expired_replacement_signals(
        item_signals=item_signals,
        include_expired_replacements=include_expired_replacements,
    )
    meal_gap_signals = list(meal_result.get("signals", {}).get("gap_signals", []))
    meal_support_signals = _build_meal_support_signals(meal_result)
    data_quality_signals = _build_data_quality_signals(item_signals)

    candidates: CandidateMap = {}

    for signal in stock_attention_signals:
        _merge_candidate(
            candidates,
            _candidate_from_stock_attention_signal(signal),
            source="stock_attention_signal",
        )

    for signal in expired_replacement_signals:
        _merge_candidate(
            candidates,
            _candidate_from_expired_replacement_signal(signal),
            source="expired_replacement_signal",
        )

    if include_meal_gap_candidates:
        for signal in meal_gap_signals:
            if _gap_is_optional_upgrade(signal) and not include_optional_upgrades:
                continue
            _merge_candidate(
                candidates,
                _candidate_from_meal_gap_signal(signal),
                source="meal_gap_signal",
            )

    if include_optional_upgrades:
        for signal in _build_generic_role_gap_signals(meal_result, item_signals):
            _merge_candidate(
                candidates,
                _candidate_from_generic_role_gap_signal(signal),
                source="generic_role_gap_signal",
            )
            meal_gap_signals.append(signal)

    suggestions = [_finalise_candidate(candidate) for candidate in candidates.values()]
    suggestions = _rank_suggestions(suggestions)

    limited = len(suggestions) > max_suggestions
    suggestions = suggestions[:max_suggestions]

    if not suggestions:
        warnings.append(
            build_warning(
                warning_type="no_restock_suggestions",
                severity="low",
                message="No restock suggestion drafts could be prepared from the selected signals.",
                agent_guidance="Do not force a shopping recommendation. Explain that there were no clear restock candidates.",
            )
        )

    if limited:
        warnings.append(
            build_warning(
                warning_type="max_suggestions_limited",
                severity="low",
                message=f"Restock suggestions were limited to max_suggestions={max_suggestions}.",
                agent_guidance="Only present the returned suggestions unless the user asks for more.",
            )
        )

    if suggestions and all(suggestion["confidence"] == "low" for suggestion in suggestions):
        warnings.append(
            build_warning(
                warning_type="low_confidence_restock_suggestions_only",
                severity="medium",
                message="Only low-confidence restock suggestion drafts could be prepared.",
                agent_guidance="Present these as tentative shopping ideas, not confident recommendations.",
            )
        )

    for meal_warning in meal_result.get("warnings", []):
        if meal_warning.get("warning_type") in {
            "no_meal_suggestions",
            "low_confidence_suggestions_only",
            "max_suggestions_limited",
        }:
            warnings.append(
                {
                    **meal_warning,
                    "warning_type": f"meal_context_{meal_warning.get('warning_type')}",
                }
            )

    candidate_merge_signals = _build_candidate_merge_signals(candidates)

    return _build_response(
        inputs=inputs,
        suggestions=suggestions,
        warnings=warnings,
        records_checked=len(item_signals),
        reference_day=reference_day,
        stock_attention_signals=stock_attention_signals,
        expired_replacement_signals=expired_replacement_signals,
        meal_gap_signals=meal_gap_signals,
        meal_support_signals=meal_support_signals,
        candidate_merge_signals=candidate_merge_signals,
        data_quality_signals=data_quality_signals,
    )


def _build_response(
    *,
    inputs: dict[str, Any],
    suggestions: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    records_checked: int,
    reference_day: date,
    stock_attention_signals: list[dict[str, Any]],
    expired_replacement_signals: list[dict[str, Any]],
    meal_gap_signals: list[dict[str, Any]],
    meal_support_signals: list[dict[str, Any]],
    candidate_merge_signals: list[dict[str, Any]],
    data_quality_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "tool_name": "draft_restock_suggestions",
        "summary": (
            f"Prepared {len(suggestions)} restock suggestion draft(s) from inventory "
            "and meal-gap signals. No records were changed."
        ),
        "result_type": "restock_suggestion_draft",
        "status": "success",
        "inputs": inputs,
        "signals": {
            "stock_attention_signals": stock_attention_signals,
            "expired_replacement_signals": expired_replacement_signals,
            "meal_gap_signals": meal_gap_signals,
            "meal_support_signals": meal_support_signals,
            "candidate_merge_signals": candidate_merge_signals,
            "data_quality_signals": data_quality_signals,
        },
        "suggestions": suggestions,
        "warnings": warnings,
        "next_actions": _build_next_actions(bool(suggestions)),
        "safety": build_safety_metadata(requires_confirmation=True),
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "version": RESTOCK_VERSION,
            "quality_refinement_version": RECOMMENDATION_QUALITY_VERSION,
            "source_tools": ["draft_meal_suggestions"],
            "records_checked": {
                "inventory": records_checked,
                "intake_history": 0,
                "intake_items": 0,
                "consumption": 0,
                "waste": 0,
            },
            "reference_date": reference_day.isoformat(),
        },
    }


def _build_item_restock_signals(
    *,
    inventory_df: pd.DataFrame,
    today: date,
    use_soon_days: int,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for _, row in inventory_df.fillna("").iterrows():
        food_item = normalize_text(row.get("food_item", ""))
        if not food_item:
            continue

        stock_status = normalize_stock_status(row.get("stock_status", ""))
        quantity = _safe_float_or_none(row.get("quantity", ""))
        servings_remaining = _safe_float_or_none(row.get("servings_remaining", ""))
        expiry_text = normalize_text(row.get("expiry_date", ""))
        expiry_classification = classify_expiry(
            expiry_text,
            today=today,
            use_soon_days=use_soon_days,
        )
        parsed_expiry_date = safe_parse_date(expiry_text)
        expiry_days = days_until(parsed_expiry_date, today=today)
        effective_stock_status = (
            "expired"
            if stock_status == "expired" or expiry_classification == "expired"
            else stock_status
        )

        roles = _infer_roles(
            food_item=food_item,
            category=normalize_text(row.get("category", "")),
        )

        signals.append(
            {
                "stock_id": normalize_text(row.get("stock_id", "")),
                "food_item": food_item,
                "brand": normalize_text(row.get("brand", "")),
                "category": normalize_text(row.get("category", "")),
                "location": normalize_text(row.get("location", "")),
                "stock_status": stock_status,
                "effective_stock_status": effective_stock_status,
                "quantity": quantity,
                "unit": normalize_text(row.get("unit", "")),
                "servings_remaining": servings_remaining,
                "expiry_date": expiry_text,
                "expiry_classification": expiry_classification,
                "days_until_expiry": expiry_days,
                "roles": roles,
            }
        )

    return signals


def _build_stock_attention_signals(
    *,
    item_signals: list[dict[str, Any]],
    include_low_stock: bool,
    include_out_of_stock: bool,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for item in item_signals:
        status = item["effective_stock_status"]
        is_low = status in LOW_STOCK_STATUSES or _is_serving_low(item)
        is_out = status == OUT_OF_STOCK_STATUS

        if is_low and include_low_stock:
            signal_type = "very_low_stock" if status == "very_low" else "low_stock"
        elif is_out and include_out_of_stock:
            signal_type = "out_of_stock"
        else:
            continue

        signals.append(
            {
                "signal_type": signal_type,
                "food_item": item["food_item"],
                "stock_id": item["stock_id"],
                "current_status": status,
                "category": item["category"],
                "roles": item["roles"],
                "source_values": {
                    "stock_status": item["stock_status"],
                    "quantity": item["quantity"],
                    "servings_remaining": item["servings_remaining"],
                },
                "message": _stock_attention_message(item=item, signal_type=signal_type),
            }
        )

    return signals


def _build_expired_replacement_signals(
    *,
    item_signals: list[dict[str, Any]],
    include_expired_replacements: bool,
) -> list[dict[str, Any]]:
    if not include_expired_replacements:
        return []

    signals: list[dict[str, Any]] = []

    for item in item_signals:
        if item["effective_stock_status"] != EXPIRED_STOCK_STATUS:
            continue

        signals.append(
            {
                "signal_type": "expired_replacement",
                "food_item": item["food_item"],
                "stock_id": item["stock_id"],
                "current_status": "expired",
                "category": item["category"],
                "roles": item["roles"],
                "expiry_date": item["expiry_date"],
                "days_until_expiry": item["days_until_expiry"],
                "message": f"{item['food_item']} appears expired and may need replacement if still wanted.",
            }
        )

    return signals


def _build_meal_support_signals(meal_result: dict[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for suggestion in meal_result.get("suggestions", []):
        signals.append(
            {
                "signal_type": "meal_opportunity_support",
                "meal_name": suggestion.get("meal_name", ""),
                "template_id": suggestion.get("template_id", ""),
                "template_name": suggestion.get("template_name", ""),
                "priority": suggestion.get("priority", ""),
                "confidence": suggestion.get("confidence", ""),
                "main_items_used": suggestion.get("main_items_used", []),
                "missing_or_low_items": suggestion.get("missing_or_low_items", []),
                "message": "Meal opportunity used as supporting context for restock suggestions.",
            }
        )

    return signals


def _build_generic_role_gap_signals(
    meal_result: dict[str, Any],
    item_signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Create cautious role-level gaps without inventing exact groceries."""
    known_roles = {
        role
        for item in item_signals
        for role in item.get("roles", [])
        if role != "unknown"
    }
    signals: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    template_lookup = {template["template_id"]: template for template in MEAL_TEMPLATES}

    for meal_signal in meal_result.get("signals", {}).get("meal_match_signals", []):
        template_id = meal_signal.get("template_id", "")
        template = template_lookup.get(template_id)
        if not template:
            continue

        matched_roles = set(meal_signal.get("matched_roles", []))
        meal_name = meal_signal.get("meal_name", "")
        missing_supporting_roles = set(template["supporting_roles"]) - matched_roles
        missing_optional_roles = set(template["optional_roles"]) - matched_roles

        for role in sorted(missing_supporting_roles):
            if role in known_roles:
                continue
            key = (meal_name, role)
            if key in seen:
                continue
            seen.add(key)
            signals.append(_generic_role_gap_signal(role, meal_signal, "supporting"))

        for role in sorted(missing_optional_roles):
            if role in known_roles or role == "seasoning":
                continue
            key = (meal_name, role)
            if key in seen:
                continue
            seen.add(key)
            signals.append(_generic_role_gap_signal(role, meal_signal, "optional"))

    return signals[:5]


def _generic_role_gap_signal(
    role: str,
    meal_signal: dict[str, Any],
    requiredness: str,
) -> dict[str, Any]:
    gap_type = (
        "generic_supporting_role_gap"
        if requiredness == "supporting"
        else "generic_optional_role_gap"
    )
    item_name = ROLE_LABELS.get(role, f"{role} option")
    meal_name = meal_signal.get("meal_name", "")
    return {
        "food_item": item_name,
        "stock_id": "",
        "gap_type": gap_type,
        "roles": [role],
        "template_id": meal_signal.get("template_id", ""),
        "template_name": meal_signal.get("template_name", ""),
        "meal_name": meal_name,
        "matched_roles": meal_signal.get("matched_roles", []),
        "gap_role": role,
        "requiredness": requiredness,
        "message": f"A {item_name} could {'support' if requiredness == 'supporting' else 'improve'} {meal_name}, but no exact tracked item was identified.",
    }


def _candidate_from_stock_attention_signal(signal: dict[str, Any]) -> dict[str, Any]:
    status = signal.get("current_status", "")
    return _base_candidate(
        item_name=signal["food_item"],
        candidate_type="exact_item_restock",
        current_status=status,
        category=signal.get("category", ""),
        roles=signal.get("roles", []),
        source_stock_ids=[signal.get("stock_id", "")],
        reasons=[signal.get("message", "Item needs stock attention.")],
        source_signal_types=[signal.get("signal_type", "stock_attention")],
        score=STOCK_STATUS_WEIGHTS.get(status, 20),
    )


def _candidate_from_expired_replacement_signal(signal: dict[str, Any]) -> dict[str, Any]:
    return _base_candidate(
        item_name=signal["food_item"],
        candidate_type="expired_replacement",
        current_status="expired",
        category=signal.get("category", ""),
        roles=signal.get("roles", []),
        source_stock_ids=[signal.get("stock_id", "")],
        reasons=[signal.get("message", "Item appears expired and may need replacement.")],
        source_signal_types=["expired_replacement"],
        score=STOCK_STATUS_WEIGHTS["expired"],
    )


def _candidate_from_meal_gap_signal(signal: dict[str, Any]) -> dict[str, Any]:
    gap_type = signal.get("gap_type", "meal_gap")
    candidate_type = (
        "expired_replacement"
        if gap_type == "expired_optional"
        else "meal_gap_restock"
    )
    requiredness = signal.get("requiredness") or _requiredness_from_gap_type(gap_type)
    meal_name = normalize_text(signal.get("meal_name", ""))
    score = GAP_TYPE_WEIGHTS.get(gap_type, 5)

    candidate = _base_candidate(
        item_name=signal.get("food_item", ""),
        candidate_type=candidate_type,
        current_status=_status_from_gap_type(gap_type),
        category="",
        roles=signal.get("roles", []),
        source_stock_ids=[signal.get("stock_id", "")],
        reasons=[signal.get("message", "Item appears in a meal gap signal.")],
        source_signal_types=[gap_type],
        score=score,
    )
    _add_meal_support(candidate, meal_name, requiredness)
    return candidate


def _candidate_from_generic_role_gap_signal(signal: dict[str, Any]) -> dict[str, Any]:
    requiredness = signal.get("requiredness", "optional")
    meal_name = normalize_text(signal.get("meal_name", ""))
    candidate = _base_candidate(
        item_name=signal.get("food_item", ""),
        candidate_type="generic_role_gap",
        current_status="unknown",
        category="",
        roles=signal.get("roles", []),
        source_stock_ids=[],
        reasons=[signal.get("message", "A generic role-level grocery option may support meal planning.")],
        source_signal_types=[signal.get("gap_type", "generic_role_gap")],
        score=GAP_TYPE_WEIGHTS.get(signal.get("gap_type", ""), 3),
    )
    _add_meal_support(candidate, meal_name, requiredness)
    return candidate


def _base_candidate(
    *,
    item_name: str,
    candidate_type: str,
    current_status: str,
    category: str,
    roles: list[str],
    source_stock_ids: list[str],
    reasons: list[str],
    source_signal_types: list[str],
    score: int,
) -> dict[str, Any]:
    return {
        "item_name": item_name,
        "candidate_type": candidate_type,
        "current_status": current_status,
        "category": category,
        "roles": sorted(set(roles)),
        "source_stock_ids": [stock_id for stock_id in source_stock_ids if stock_id],
        "source_signal_types": source_signal_types,
        "reasons": reasons,
        "supports_meals": [],
        "blocking_meal_count": 0,
        "supporting_meal_count": 0,
        "optional_meal_count": 0,
        "score": score,
        "merge_sources": [],
    }


def _merge_candidate(candidates: CandidateMap, candidate: dict[str, Any], *, source: str) -> None:
    key = _candidate_key(candidate)

    if key not in candidates:
        candidate["merge_sources"] = [source]
        candidates[key] = candidate
        return

    existing = candidates[key]
    existing["candidate_type"] = _stronger_candidate_type(
        existing.get("candidate_type", ""),
        candidate.get("candidate_type", ""),
    )
    existing["current_status"] = _stronger_status(
        existing.get("current_status", ""),
        candidate.get("current_status", ""),
    )
    existing["category"] = existing.get("category") or candidate.get("category", "")
    existing["roles"] = sorted(set(existing.get("roles", [])) | set(candidate.get("roles", [])))
    existing["source_stock_ids"] = sorted(
        set(existing.get("source_stock_ids", [])) | set(candidate.get("source_stock_ids", []))
    )
    existing["source_signal_types"] = sorted(
        set(existing.get("source_signal_types", [])) | set(candidate.get("source_signal_types", []))
    )
    existing["reasons"] = _unique_preserve_order(existing.get("reasons", []) + candidate.get("reasons", []))
    existing["supports_meals"] = _unique_preserve_order(
        existing.get("supports_meals", []) + candidate.get("supports_meals", [])
    )
    existing["blocking_meal_count"] += candidate.get("blocking_meal_count", 0)
    existing["supporting_meal_count"] += candidate.get("supporting_meal_count", 0)
    existing["optional_meal_count"] += candidate.get("optional_meal_count", 0)
    existing["score"] += candidate.get("score", 0)
    existing["merge_sources"] = _unique_preserve_order(existing.get("merge_sources", []) + [source])


def _finalise_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    confidence = _confidence_from_candidate(candidate)
    quality_fields = restock_quality_fields(candidate, confidence=confidence)
    score = quality_fields["score"]
    priority = _priority_from_score(score)
    suggested_action = _suggested_action(candidate)

    return {
        "item_name": candidate["item_name"],
        "suggestion_type": "restock",
        "candidate_type": candidate["candidate_type"],
        "priority": priority,
        "confidence": confidence,
        "score": score,
        "current_status": candidate.get("current_status", "unknown"),
        "category": candidate.get("category", ""),
        "roles": candidate.get("roles", []),
        "source_stock_ids": candidate.get("source_stock_ids", []),
        "source_signal_types": candidate.get("source_signal_types", []),
        "supports_meals": candidate.get("supports_meals", []),
        "blocking_meal_count": candidate.get("blocking_meal_count", 0),
        "supporting_meal_count": candidate.get("supporting_meal_count", 0),
        "optional_meal_count": candidate.get("optional_meal_count", 0),
        "reasons": candidate.get("reasons", []),
        "reason": _single_reason(candidate),
        "suggested_action": suggested_action,
        "would_create_shopping_list_record": False,
        "requires_user_confirmation_before_write": True,
        **quality_fields,
    }


def _build_candidate_merge_signals(candidates: CandidateMap) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for candidate in candidates.values():
        signals.append(
            {
                "signal_type": "restock_candidate_merge",
                "item_name": candidate.get("item_name", ""),
                "candidate_type": candidate.get("candidate_type", ""),
                "source_signal_types": candidate.get("source_signal_types", []),
                "supports_meals": candidate.get("supports_meals", []),
                "score_before_priority_mapping": _capped_score(candidate),
                "message": "Restock candidate built by merging stock, expiry, and/or meal-gap evidence.",
            }
        )

    return signals


def _build_data_quality_signals(item_signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for item in item_signals:
        if not item.get("stock_status") or item.get("stock_status") == "unknown":
            signals.append(
                {
                    "signal_type": "missing_or_unknown_stock_status",
                    "severity": "low",
                    "stock_id": item.get("stock_id", ""),
                    "food_item": item.get("food_item", ""),
                    "message": "Stock status is missing or unknown, which reduces restock confidence.",
                }
            )

        if item.get("expiry_classification") == "invalid_expiry_date":
            signals.append(
                {
                    "signal_type": "invalid_expiry_date",
                    "severity": "medium",
                    "stock_id": item.get("stock_id", ""),
                    "food_item": item.get("food_item", ""),
                    "message": "Expiry date could not be parsed, which reduces freshness confidence.",
                }
            )

        if item.get("roles") == ["unknown"]:
            signals.append(
                {
                    "signal_type": "unknown_food_role",
                    "severity": "low",
                    "stock_id": item.get("stock_id", ""),
                    "food_item": item.get("food_item", ""),
                    "message": "Food role could not be confidently inferred, which limits meal-aware restock reasoning.",
                }
            )

    return signals


def _build_next_actions(has_suggestions: bool) -> list[dict[str, Any]]:
    if not has_suggestions:
        return [
            build_next_action(
                action_type="add_inventory_detail",
                label="Add or improve inventory records",
                tool_name="add_inventory_item",
                reason="More inventory detail would make restock suggestions more useful.",
                requires_confirmation=True,
            )
        ]

    return [
        build_next_action(
            action_type="confirm_restock_draft",
            label="Ask the user which restock suggestions they want to act on",
            tool_name="future_confirmed_shopping_list_workflow",
            reason="Version 1.5D only drafts shopping-list ideas; persistent shopping-list writes are deferred.",
            requires_confirmation=True,
        )
    ]


def _stock_attention_message(*, item: dict[str, Any], signal_type: str) -> str:
    if signal_type == "out_of_stock":
        return f"{item['food_item']} is marked out of stock."
    if signal_type == "very_low_stock":
        return f"{item['food_item']} is marked very low."
    return f"{item['food_item']} is marked low or appears to have very few servings remaining."


def _infer_roles(*, food_item: str, category: str) -> list[str]:
    # Backward-compatible wrapper retained for local helper callers.
    return infer_food_roles(food_item=food_item, category=category)["roles"]


def _add_meal_support(candidate: dict[str, Any], meal_name: str, requiredness: str) -> None:
    if meal_name:
        candidate["supports_meals"] = _unique_preserve_order(candidate.get("supports_meals", []) + [meal_name])

    if requiredness == "blocking":
        candidate["blocking_meal_count"] += 1
    elif requiredness == "supporting":
        candidate["supporting_meal_count"] += 1
    else:
        candidate["optional_meal_count"] += 1


def _requiredness_from_gap_type(gap_type: str) -> str:
    if gap_type == "low_stock_used":
        return "supporting"
    if gap_type in {"generic_supporting_role_gap"}:
        return "supporting"
    return "optional"


def _status_from_gap_type(gap_type: str) -> str:
    if gap_type in {"out_of_stock_optional"}:
        return "out"
    if gap_type in {"expired_optional"}:
        return "expired"
    if gap_type in {"low_stock_used", "low_stock_optional"}:
        return "low"
    return "unknown"


def _gap_is_optional_upgrade(signal: dict[str, Any]) -> bool:
    return _requiredness_from_gap_type(signal.get("gap_type", "")) == "optional"


def _candidate_key(candidate: dict[str, Any]) -> str:
    return normalize_text(candidate.get("item_name", "")).lower()


def _stronger_candidate_type(first: str, second: str) -> str:
    order = {
        "generic_role_gap": 1,
        "meal_gap_restock": 2,
        "exact_item_restock": 3,
        "expired_replacement": 4,
    }
    return first if order.get(first, 0) >= order.get(second, 0) else second


def _stronger_status(first: str, second: str) -> str:
    order = {"unknown": 0, "low": 1, "very_low": 2, "expired": 3, "out": 4}
    return first if order.get(first, 0) >= order.get(second, 0) else second


def _capped_score(candidate: dict[str, Any]) -> int:
    score = int(candidate.get("score", 0))

    if candidate.get("source_stock_ids"):
        score += 10
    if candidate.get("candidate_type") == "generic_role_gap":
        score -= 10

    score += 5 * len(candidate.get("supports_meals", []))
    score += 18 * candidate.get("blocking_meal_count", 0)
    score += 10 * candidate.get("supporting_meal_count", 0)
    score += 5 * candidate.get("optional_meal_count", 0)

    return max(score, 0)


def _priority_from_score(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def _confidence_from_candidate(candidate: dict[str, Any]) -> str:
    if candidate.get("candidate_type") == "generic_role_gap":
        return "low"

    has_exact_item = bool(candidate.get("source_stock_ids"))
    has_meal_support = bool(candidate.get("supports_meals"))

    if has_exact_item and has_meal_support:
        return "high"
    if has_exact_item:
        return "medium"
    return "low"


def _suggested_action(candidate: dict[str, Any]) -> str:
    item_name = candidate.get("item_name", "this item")
    candidate_type = candidate.get("candidate_type", "")

    if candidate_type == "expired_replacement":
        return f"Consider replacing {item_name} if the user still wants to keep it available."
    if candidate_type == "generic_role_gap":
        return f"Consider whether the user wants to add a {item_name}; do not treat this as a confirmed shopping-list item."
    return f"Consider restocking {item_name}."


def _single_reason(candidate: dict[str, Any]) -> str:
    reasons = candidate.get("reasons", [])
    supports_meals = candidate.get("supports_meals", [])

    if supports_meals:
        meal_text = ", ".join(supports_meals[:3])
        return f"{reasons[0] if reasons else 'Item has restock evidence.'} It also supports: {meal_text}."

    return reasons[0] if reasons else "Item has restock evidence."


def _rank_suggestions(suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority_score = {"high": 3, "medium": 2, "low": 1}
    confidence_score = {"high": 3, "medium": 2, "low": 1}

    return sorted(
        suggestions,
        key=lambda suggestion: (
            -priority_score.get(suggestion.get("priority", ""), 0),
            -suggestion.get("score", 0),
            -confidence_score.get(suggestion.get("confidence", ""), 0),
            suggestion.get("item_name", "").lower(),
        ),
    )


def _empty_meal_result() -> dict[str, Any]:
    return {
        "signals": {
            "gap_signals": [],
            "meal_match_signals": [],
        },
        "suggestions": [],
        "warnings": [],
    }


def _resolve_reference_date(reference_date: str) -> date:
    text = normalize_text(reference_date)
    if not text:
        return date.today()

    parsed = safe_parse_date(text)
    return parsed or date.today()


def _safe_float_or_none(value: Any) -> float | None:
    text = normalize_text(value)

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _is_serving_low(item: dict[str, Any]) -> bool:
    servings = item.get("servings_remaining")
    return servings is not None and 0 < servings <= 1


def _unique_preserve_order(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    unique: list[Any] = []

    for value in values:
        if value in seen or value in {"", None}:
            continue
        seen.add(value)
        unique.append(value)

    return unique
