"""Recommendation quality helpers for Grocery Assistant MCP Version 1.5E.

These helpers enrich read-only meal and restock drafts with consistent quality
metadata. They do not read or write CSV files and should remain pure helper
logic.
"""

from __future__ import annotations

from typing import Any

RECOMMENDATION_QUALITY_VERSION = "1.5E"

ROLE_KEYWORDS: dict[str, set[str]] = {
    "protein": {
        "chicken",
        "beef",
        "mince",
        "steak",
        "pork",
        "turkey",
        "fish",
        "tuna",
        "salmon",
        "egg",
        "eggs",
        "tofu",
        "beans",
        "lentils",
        "chickpea",
        "chickpeas",
    },
    "base": {
        "rice",
        "pasta",
        "noodle",
        "noodles",
        "quinoa",
        "couscous",
        "potato",
        "potatoes",
        "oats",
    },
    "bread_wrap": {
        "bread",
        "wrap",
        "wraps",
        "tortilla",
        "tortillas",
        "roll",
        "rolls",
        "toast",
    },
    "vegetable": {
        "spinach",
        "lettuce",
        "tomato",
        "tomatoes",
        "carrot",
        "carrots",
        "broccoli",
        "vegetable",
        "vegetables",
        "onion",
        "capsicum",
        "mushroom",
        "mushrooms",
        "cucumber",
        "zucchini",
        "peas",
        "corn",
    },
    "fruit": {
        "apple",
        "apples",
        "banana",
        "bananas",
        "berries",
        "strawberry",
        "strawberries",
        "blueberry",
        "blueberries",
    },
    "dairy": {
        "cheese",
        "milk",
        "yoghurt",
        "yogurt",
        "cream",
        "butter",
    },
    "sauce": {
        "sauce",
        "salsa",
        "pesto",
        "mayo",
        "mayonnaise",
        "aioli",
        "soy sauce",
        "dressing",
        "curry paste",
    },
    "seasoning": {
        "salt",
        "pepper",
        "spice",
        "spices",
        "herbs",
        "seasoning",
    },
}

CATEGORY_ROLE_MAP: dict[str, str] = {
    "protein": "protein",
    "meat": "protein",
    "seafood": "protein",
    "pantry": "base",
    "grain": "base",
    "grains": "base",
    "vegetable": "vegetable",
    "vegetables": "vegetable",
    "produce": "vegetable",
    "fruit": "fruit",
    "dairy": "dairy",
    "sauce": "sauce",
    "condiment": "sauce",
    "condiments": "sauce",
    "spice": "seasoning",
    "spices": "seasoning",
    "seasoning": "seasoning",
    "bakery": "bread_wrap",
    "bread": "bread_wrap",
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
    "unknown": "unclassified item",
}


def infer_food_roles(*, food_item: str, category: str = "") -> dict[str, Any]:
    """Infer simple food roles with explicit evidence metadata."""
    item_text = str(food_item or "").strip().lower()
    category_text = str(category or "").strip().lower()

    roles: set[str] = set()
    role_sources: list[str] = []
    assumptions: list[str] = []

    if category_text in CATEGORY_ROLE_MAP:
        roles.add(CATEGORY_ROLE_MAP[category_text])
        role_sources.append("category")

    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in item_text:
                roles.add(role)
                if "item_name" not in role_sources:
                    role_sources.append("item_name")
                break

    if not roles:
        roles.add("unknown")
        confidence = "low"
        assumptions.append("Food role could not be inferred from category or item name.")
    elif "category" in role_sources and "item_name" in role_sources:
        confidence = "high"
    else:
        confidence = "medium"
        assumptions.append("Food role is inferred from limited item metadata.")

    return {
        "roles": sorted(roles),
        "role_confidence": confidence,
        "role_sources": role_sources,
        "role_assumptions": assumptions,
    }


def quality_level_from_missing_fields(missing_fields: list[str]) -> str:
    """Classify whether a record is complete enough for soft recommendation work."""
    missing = set(missing_fields)
    if not missing:
        return "complete"
    if missing <= {"expiry_date"}:
        return "usable_with_minor_gaps"
    if missing <= {"quantity", "unit", "servings_remaining", "expiry_date"}:
        return "usable_for_soft_suggestion_only"
    return "low_quality"


def assumption_level(*, role_confidence: str, data_quality: str) -> str:
    if role_confidence == "low" or data_quality in {"low_quality", "not_usable_for_this_task"}:
        return "high"
    if role_confidence == "medium" or data_quality == "usable_for_soft_suggestion_only":
        return "medium"
    return "low"


def recommendation_risk(*, confidence: str, assumption: str) -> str:
    if confidence == "low" or assumption == "high":
        return "medium"
    return "low"


def meal_score_breakdown(
    *,
    main_items: list[dict[str, Any]],
    use_soon_items: list[str],
    gap_signals: list[dict[str, Any]],
    confidence: str,
) -> dict[str, int]:
    availability_score = 10 + min(len(main_items), 4) * 5
    use_soon_score = 20 if use_soon_items else 0
    completeness_score = 20 if len(main_items) >= 3 else 10 if len(main_items) >= 2 else 0
    gap_penalty = -5 * len([gap for gap in gap_signals if gap.get("gap_type") != "low_stock_used"])
    data_quality_penalty = -5 * sum(1 for item in main_items if item.get("roles") == ["unknown"])
    confidence_adjustment = {"high": 10, "medium": 5, "low": 0}.get(confidence, 0)
    return {
        "availability_score": availability_score,
        "use_soon_score": use_soon_score,
        "meal_completeness_score": completeness_score,
        "gap_penalty": gap_penalty,
        "data_quality_penalty": data_quality_penalty,
        "confidence_adjustment": confidence_adjustment,
    }


def score_from_breakdown(score_breakdown: dict[str, int]) -> int:
    return max(int(sum(score_breakdown.values())), 0)


def match_quality_from_meal(*, main_items: list[dict[str, Any]], confidence: str) -> str:
    if confidence == "high" and len(main_items) >= 3:
        return "strong_match"
    if len(main_items) >= 2:
        return "usable_match"
    return "partial_match"


def meal_quality_fields(match: dict[str, Any]) -> dict[str, Any]:
    """Build backward-compatible quality fields for a meal suggestion."""
    main_items = match.get("main_items", [])
    gap_signals = match.get("gap_signals", [])
    use_soon_items = match.get("use_soon_items_used", [])
    confidence = match.get("confidence", "low")

    missing_fields: list[str] = []
    for item in main_items:
        if item.get("quantity") is None and item.get("servings_remaining") is None:
            missing_fields.extend(["quantity", "servings_remaining"])
        if not item.get("unit"):
            missing_fields.append("unit")
        if item.get("expiry_parse_status") == "missing":
            missing_fields.append("expiry_date")

    data_quality = quality_level_from_missing_fields(sorted(set(missing_fields)))
    weakest_role_confidence = _weakest_role_confidence(main_items)
    assumption = assumption_level(
        role_confidence=weakest_role_confidence,
        data_quality=data_quality,
    )
    score_breakdown = meal_score_breakdown(
        main_items=main_items,
        use_soon_items=use_soon_items,
        gap_signals=gap_signals,
        confidence=confidence,
    )
    score = score_from_breakdown(score_breakdown)

    evidence_summary = _meal_evidence_summary(
        match=match,
        main_items=main_items,
        use_soon_items=use_soon_items,
        gap_signals=gap_signals,
    )
    limitations = _meal_limitations(missing_fields=sorted(set(missing_fields)), gap_signals=gap_signals)

    return {
        "score": score,
        "score_breakdown": score_breakdown,
        "match_quality": match_quality_from_meal(main_items=main_items, confidence=confidence),
        "data_quality": data_quality,
        "assumption_level": assumption,
        "recommendation_risk": recommendation_risk(confidence=confidence, assumption=assumption),
        "evidence_summary": evidence_summary,
        "limitations": limitations,
        "agent_guidance": "Present this as a draft meal opportunity, not a logged meal or inventory action.",
    }


def restock_score_breakdown(candidate: dict[str, Any]) -> dict[str, int]:
    stock_urgency_score = _stock_urgency_score(candidate)
    meal_support_score = (
        18 * int(candidate.get("blocking_meal_count", 0))
        + 10 * int(candidate.get("supporting_meal_count", 0))
        + 5 * int(candidate.get("optional_meal_count", 0))
        + 5 * len(candidate.get("supports_meals", []))
    )
    evidence_quality_score = 10 if candidate.get("source_stock_ids") else 0
    generic_role_penalty = -10 if candidate.get("candidate_type") == "generic_role_gap" else 0
    data_quality_penalty = -5 if candidate.get("roles") == ["unknown"] else 0
    return {
        "stock_urgency_score": stock_urgency_score,
        "meal_support_score": meal_support_score,
        "evidence_quality_score": evidence_quality_score,
        "generic_role_penalty": generic_role_penalty,
        "data_quality_penalty": data_quality_penalty,
    }


def restock_quality_fields(candidate: dict[str, Any], *, confidence: str) -> dict[str, Any]:
    score_breakdown = restock_score_breakdown(candidate)
    score = score_from_breakdown(score_breakdown)
    data_quality = "usable_with_minor_gaps"
    if candidate.get("candidate_type") == "generic_role_gap":
        data_quality = "usable_for_soft_suggestion_only"
    if candidate.get("roles") == ["unknown"]:
        data_quality = "low_quality"

    role_confidence = "low" if candidate.get("roles") == ["unknown"] else "medium"
    if candidate.get("source_stock_ids") and candidate.get("roles") != ["unknown"]:
        role_confidence = "high"

    assumption = assumption_level(role_confidence=role_confidence, data_quality=data_quality)

    return {
        "score": score,
        "score_breakdown": score_breakdown,
        "data_quality": data_quality,
        "assumption_level": assumption,
        "recommendation_risk": recommendation_risk(confidence=confidence, assumption=assumption),
        "evidence_summary": _restock_evidence_summary(candidate),
        "limitations": _restock_limitations(candidate),
        "agent_guidance": "Present this as a draft restock idea that still needs user confirmation before any write action.",
    }


def _weakest_role_confidence(items: list[dict[str, Any]]) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    weakest = "high"
    for item in items:
        confidence = item.get("role_confidence", "medium")
        if order.get(confidence, 1) < order.get(weakest, 2):
            weakest = confidence
    return weakest


def _meal_evidence_summary(
    *,
    match: dict[str, Any],
    main_items: list[dict[str, Any]],
    use_soon_items: list[str],
    gap_signals: list[dict[str, Any]],
) -> list[str]:
    evidence = [
        f"Matched the {match.get('template_name', 'meal')} template using: "
        f"{', '.join(item.get('food_item', '') for item in main_items if item.get('food_item'))}."
    ]
    if use_soon_items:
        evidence.append(f"Use-soon item(s) increase priority: {', '.join(use_soon_items)}.")
    if gap_signals:
        gap_names = ", ".join(gap.get("food_item", "") for gap in gap_signals if gap.get("food_item"))
        evidence.append(f"Gap hint(s) were found but do not block the meal: {gap_names}.")
    return evidence


def _meal_limitations(*, missing_fields: list[str], gap_signals: list[dict[str, Any]]) -> list[str]:
    limitations: list[str] = []
    if missing_fields:
        limitations.append(
            "Some inventory fields are missing, so this is a soft suggestion rather than a precise serving calculation."
        )
    if any(gap.get("gap_type") == "expired_optional" for gap in gap_signals):
        limitations.append("Expired gap items should not be treated as usable ingredients.")
    if any(gap.get("gap_type") == "out_of_stock_optional" for gap in gap_signals):
        limitations.append("Out-of-stock gap items may improve the meal but are not currently available.")
    return limitations


def _restock_evidence_summary(candidate: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    for reason in candidate.get("reasons", [])[:3]:
        if reason:
            evidence.append(reason)
    if candidate.get("supports_meals"):
        evidence.append(
            "Supports meal opportunity/opportunities: "
            + ", ".join(candidate.get("supports_meals", [])[:3])
            + "."
        )
    if candidate.get("candidate_type") == "generic_role_gap":
        evidence.append("This is a generic role gap, not an exact known inventory item.")
    return evidence


def _restock_limitations(candidate: dict[str, Any]) -> list[str]:
    limitations: list[str] = []
    if candidate.get("candidate_type") == "generic_role_gap":
        limitations.append("Do not invent a specific grocery item unless the user confirms one.")
    if not candidate.get("source_stock_ids"):
        limitations.append("No exact tracked inventory item supports this candidate.")
    if candidate.get("current_status") == "expired":
        limitations.append("Expired items should be replaced only if the user still wants that item available.")
    return limitations


def _stock_urgency_score(candidate: dict[str, Any]) -> int:
    if candidate.get("candidate_type") == "expired_replacement":
        return 35
    return {
        "out": 40,
        "very_low": 30,
        "low": 20,
        "expired": 35,
        "unknown": 0,
    }.get(str(candidate.get("current_status", "unknown")), 0)
