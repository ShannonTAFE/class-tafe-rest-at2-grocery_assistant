from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


AVAILABLE_STATUSES = {"in_stock", "low", "very_low", "ok", "available"}
LOW_STATUSES = {"low", "very_low"}
OUT_STATUSES = {"out", "empty", "out_of_stock"}
EXPIRED_STATUSES = {"expired"}

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

MEAL_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_id": "rice_bowl",
        "meal_name": "Rice bowl",
        "required_role": "base",
        "required_keywords": {"rice"},
        "supporting_roles": {"protein", "vegetable"},
        "optional_roles": {"sauce", "dairy", "seasoning"},
        "minimum_supporting_matches": 1,
    },
    {
        "template_id": "pasta_meal",
        "meal_name": "Pasta meal",
        "required_role": "base",
        "required_keywords": {"pasta", "noodle", "noodles"},
        "supporting_roles": {"protein", "vegetable", "dairy", "sauce"},
        "optional_roles": {"seasoning"},
        "minimum_supporting_matches": 1,
    },
    {
        "template_id": "wrap_or_sandwich",
        "meal_name": "Wrap or sandwich",
        "required_role": "bread_wrap",
        "required_keywords": set(),
        "supporting_roles": {"protein", "vegetable", "dairy", "sauce"},
        "optional_roles": {"seasoning"},
        "minimum_supporting_matches": 1,
    },
    {
        "template_id": "omelette_or_eggs",
        "meal_name": "Omelette or eggs",
        "required_role": "protein",
        "required_keywords": {"egg", "eggs"},
        "supporting_roles": {"vegetable", "dairy", "bread_wrap"},
        "optional_roles": {"sauce", "seasoning"},
        "minimum_supporting_matches": 1,
    },
    {
        "template_id": "salad_bowl",
        "meal_name": "Salad bowl",
        "required_role": "vegetable",
        "required_keywords": set(),
        "supporting_roles": {"protein", "base", "dairy"},
        "optional_roles": {"sauce", "seasoning"},
        "minimum_supporting_matches": 1,
    },
]


def build_meal_suggestion_draft(
    inventory_df: pd.DataFrame,
    *,
    include_use_soon: bool = True,
    include_inventory_based: bool = True,
    include_gap_hints: bool = True,
    max_suggestions: int = 5,
    use_soon_days: int = 3,
    reference_date: str = "",
) -> dict[str, Any]:
    """
    Build read-only meal opportunity suggestions from inventory signals.

    This helper intentionally avoids recipe generation. It creates conservative,
    explainable meal opportunity drafts from:
    - availability signals
    - expiry/use-soon signals
    - inferred food roles
    - simple meal templates
    - low/out-of-stock gap hints

    No records are changed.
    """
    inputs = {
        "include_use_soon": include_use_soon,
        "include_inventory_based": include_inventory_based,
        "include_gap_hints": include_gap_hints,
        "max_suggestions": max_suggestions,
        "use_soon_days": use_soon_days,
        "reference_date": reference_date,
    }

    warnings: list[dict[str, Any]] = []

    if max_suggestions < 1:
        max_suggestions = 1
        warnings.append(
            {
                "warning_type": "invalid_max_suggestions",
                "severity": "medium",
                "message": "max_suggestions was less than 1 and has been adjusted to 1.",
                "agent_guidance": "Continue with the adjusted limit.",
            }
        )

    today = _resolve_reference_date(reference_date)

    if inventory_df is None or inventory_df.empty:
        return _empty_result(
            inputs=inputs,
            warnings=[
                *warnings,
                {
                    "warning_type": "no_inventory_items",
                    "severity": "low",
                    "message": "No inventory items were available to draft meal suggestions.",
                    "agent_guidance": "Do not invent meal suggestions. Ask the user to add inventory items first.",
                },
            ],
        )

    item_signals = _build_item_signals(
        inventory_df=inventory_df,
        today=today,
        use_soon_days=use_soon_days,
    )

    inventory_signals = [_inventory_signal_view(signal) for signal in item_signals]
    meal_role_signals = [_role_signal_view(signal) for signal in item_signals]
    data_quality_signals = _build_data_quality_signals(item_signals)

    available_items = [item for item in item_signals if item["is_available"]]
    low_or_out_items = [
        item
        for item in item_signals
        if item["is_low_stock"] or item["availability"] in {"out", "expired"}
    ]

    suggestions: list[dict[str, Any]] = []
    meal_match_signals: list[dict[str, Any]] = []
    gap_signals: list[dict[str, Any]] = []

    if include_use_soon or include_inventory_based:
        for template in MEAL_TEMPLATES:
            matches = _match_template(
                template=template,
                available_items=available_items,
                low_or_out_items=low_or_out_items,
                include_gap_hints=include_gap_hints,
            )

            for match in matches:
                uses_use_soon = bool(match["use_soon_items_used"])

                if uses_use_soon and not include_use_soon:
                    continue

                if not uses_use_soon and not include_inventory_based:
                    continue

                meal_match_signals.append(match["meal_match_signal"])
                gap_signals.extend(match["gap_signals"])

                suggestions.append(_build_suggestion_from_match(match))

    suggestions = _deduplicate_suggestions(suggestions)
    suggestions = _rank_suggestions(suggestions)

    limited = len(suggestions) > max_suggestions
    suggestions = suggestions[:max_suggestions]

    if not suggestions:
        warnings.append(
            {
                "warning_type": "no_meal_suggestions",
                "severity": "low",
                "message": "No meal suggestions could be drafted from the available inventory signals.",
                "agent_guidance": "Do not force a recommendation. Explain that more inventory detail may be needed.",
            }
        )

    if limited:
        warnings.append(
            {
                "warning_type": "max_suggestions_limited",
                "severity": "low",
                "message": f"Meal suggestions were limited to max_suggestions={max_suggestions}.",
                "agent_guidance": "Only present the returned suggestions unless the user asks for more.",
            }
        )

    if suggestions and all(suggestion["confidence"] == "low" for suggestion in suggestions):
        warnings.append(
            {
                "warning_type": "low_confidence_suggestions_only",
                "severity": "medium",
                "message": "Only low-confidence meal suggestions could be drafted.",
                "agent_guidance": "Present these as tentative meal ideas, not confident recommendations.",
            }
        )

    return {
        "tool_name": "draft_meal_suggestions",
        "summary": (
            f"Prepared {len(suggestions)} meal suggestion draft(s) from current "
            "inventory signals. No records were changed."
        ),
        "result_type": "meal_suggestion_draft",
        "status": "success",
        "inputs": {
            **inputs,
            "max_suggestions": max_suggestions,
        },
        "signals": {
            "inventory_signals": inventory_signals,
            "meal_role_signals": meal_role_signals,
            "meal_match_signals": meal_match_signals,
            "gap_signals": gap_signals,
            "data_quality_signals": data_quality_signals,
        },
        "suggestions": suggestions,
        "warnings": warnings,
    }


def _empty_result(
    *,
    inputs: dict[str, Any],
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "tool_name": "draft_meal_suggestions",
        "summary": "Prepared 0 meal suggestion draft(s). No records were changed.",
        "result_type": "meal_suggestion_draft",
        "status": "success",
        "inputs": inputs,
        "signals": {
            "inventory_signals": [],
            "meal_role_signals": [],
            "meal_match_signals": [],
            "gap_signals": [],
            "data_quality_signals": [],
        },
        "suggestions": [],
        "warnings": warnings,
    }


def _resolve_reference_date(reference_date: str) -> date:
    if not str(reference_date).strip():
        return date.today()

    try:
        return datetime.strptime(str(reference_date).strip(), "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def _build_item_signals(
    *,
    inventory_df: pd.DataFrame,
    today: date,
    use_soon_days: int,
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for _, row in inventory_df.fillna("").iterrows():
        food_item = _safe_text(row.get("food_item", ""))
        if not food_item:
            continue

        status = _normalise_status(row.get("stock_status", ""))
        quantity = _safe_float_or_none(row.get("quantity", ""))
        servings_remaining = _safe_float_or_none(row.get("servings_remaining", ""))
        expiry_date_raw = _safe_text(row.get("expiry_date", ""))
        expiry_date, expiry_parse_status = _parse_date_or_status(expiry_date_raw)
        days_until_expiry = (
            (expiry_date - today).days if expiry_date is not None else None
        )

        is_expired_by_date = (
            days_until_expiry is not None and days_until_expiry < 0
        )
        is_expired = status in EXPIRED_STATUSES or is_expired_by_date
        is_out = status in OUT_STATUSES
        is_low_stock = status in LOW_STATUSES

        if servings_remaining is not None and 0 < servings_remaining <= 1:
            is_low_stock = True

        if status in AVAILABLE_STATUSES and not is_expired:
            availability = "available"
        elif is_expired:
            availability = "expired"
        elif is_out:
            availability = "out"
        elif _has_positive_amount(quantity) or _has_positive_amount(servings_remaining):
            availability = "available"
        else:
            availability = "unknown"

        is_available = availability == "available"

        is_use_soon = (
            is_available
            and days_until_expiry is not None
            and 0 <= days_until_expiry <= use_soon_days
        )

        roles = _infer_roles(
            food_item=food_item,
            category=_safe_text(row.get("category", "")),
        )

        signals.append(
            {
                "stock_id": _safe_text(row.get("stock_id", "")),
                "food_item": food_item,
                "brand": _safe_text(row.get("brand", "")),
                "category": _safe_text(row.get("category", "")),
                "location": _safe_text(row.get("location", "")),
                "stock_status": status,
                "quantity": quantity,
                "unit": _safe_text(row.get("unit", "")),
                "servings_remaining": servings_remaining,
                "expiry_date": expiry_date_raw,
                "expiry_parse_status": expiry_parse_status,
                "days_until_expiry": days_until_expiry,
                "availability": availability,
                "is_available": is_available,
                "is_low_stock": is_low_stock,
                "is_use_soon": is_use_soon,
                "roles": roles,
            }
        )

    return signals


def _infer_roles(*, food_item: str, category: str) -> list[str]:
    roles: set[str] = set()
    item_text = food_item.lower()
    category_text = category.lower()

    if category_text in CATEGORY_ROLE_MAP:
        roles.add(CATEGORY_ROLE_MAP[category_text])

    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in item_text:
                roles.add(role)

    if not roles:
        roles.add("unknown")

    return sorted(roles)


def _match_template(
    *,
    template: dict[str, Any],
    available_items: list[dict[str, Any]],
    low_or_out_items: list[dict[str, Any]],
    include_gap_hints: bool,
) -> list[dict[str, Any]]:
    required_candidates = [
        item
        for item in available_items
        if _item_matches_required_template_part(item=item, template=template)
    ]

    if not required_candidates:
        return []

    matches: list[dict[str, Any]] = []

    for required_item in required_candidates[:2]:
        supporting_items = [
            item
            for item in available_items
            if item["food_item"] != required_item["food_item"]
            and set(item["roles"]).intersection(template["supporting_roles"])
        ]

        if len(supporting_items) < template["minimum_supporting_matches"]:
            continue

        supporting_items = _rank_items_for_template(supporting_items)[:3]
        main_items = [required_item, *supporting_items]

        use_soon_items = [
            item["food_item"]
            for item in main_items
            if item["is_use_soon"]
        ]

        gap_signals = (
            _build_gap_signals(
                template=template,
                main_items=main_items,
                low_or_out_items=low_or_out_items,
            )
            if include_gap_hints
            else []
        )

        meal_name = _build_meal_name(
            template_name=template["meal_name"],
            main_items=main_items,
        )

        for gap_signal in gap_signals:
            gap_signal["meal_name"] = meal_name

        priority = _score_priority(
            use_soon_items=use_soon_items,
            main_items=main_items,
            gap_signals=gap_signals,
        )

        confidence = _score_confidence(
            supporting_count=len(supporting_items),
            main_items=main_items,
            gap_signals=gap_signals,
        )

        suggestion_type = (
            "use_soon_meal"
            if use_soon_items
            else "inventory_based_meal"
        )

        matched_roles = sorted(
            {
                role
                for item in main_items
                for role in item["roles"]
                if role != "unknown"
            }
        )

        meal_match_signal = {
            "template_id": template["template_id"],
            "template_name": template["meal_name"],
            "meal_name": meal_name,
            "suggestion_type": suggestion_type,
            "required_item": required_item["food_item"],
            "required_role": template["required_role"],
            "supporting_items": [item["food_item"] for item in supporting_items],
            "supporting_roles": sorted(template["supporting_roles"]),
            "optional_roles": sorted(template["optional_roles"]),
            "matched_roles": matched_roles,
            "use_soon_items_used": use_soon_items,
            "priority": priority,
            "confidence": confidence,
        }

        matches.append(
            {
                "meal_name": meal_name,
                "suggestion_type": suggestion_type,
                "template_id": template["template_id"],
                "template_name": template["meal_name"],
                "matched_roles": matched_roles,
                "priority": priority,
                "confidence": confidence,
                "main_items": main_items,
                "use_soon_items_used": use_soon_items,
                "gap_signals": gap_signals,
                "meal_match_signal": meal_match_signal,
            }
        )

    return matches


def _item_matches_required_template_part(
    *,
    item: dict[str, Any],
    template: dict[str, Any],
) -> bool:
    required_role = template["required_role"]
    required_keywords = template["required_keywords"]

    if required_role not in item["roles"]:
        return False

    if not required_keywords:
        return True

    item_name = item["food_item"].lower()
    return any(keyword in item_name for keyword in required_keywords)


def _rank_items_for_template(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            not item["is_use_soon"],
            not item["is_low_stock"],
            item["food_item"].lower(),
        ),
    )


def _build_gap_signals(
    *,
    template: dict[str, Any],
    main_items: list[dict[str, Any]],
    low_or_out_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    main_item_names = {item["food_item"] for item in main_items}
    relevant_gap_roles = set(template["supporting_roles"]).union(template["optional_roles"])

    gap_signals: list[dict[str, Any]] = []

    for item in low_or_out_items:
        if item["food_item"] in main_item_names:
            if item["is_low_stock"]:
                gap_type = "low_stock_used"
            else:
                continue
        elif not set(item["roles"]).intersection(relevant_gap_roles):
            continue
        elif item["availability"] == "out":
            gap_type = "out_of_stock_optional"
        elif item["availability"] == "expired":
            gap_type = "expired_optional"
        elif item["is_low_stock"]:
            gap_type = "low_stock_optional"
        else:
            continue

        gap_signals.append(
            {
                "food_item": item["food_item"],
                "stock_id": item["stock_id"],
                "gap_type": gap_type,
                "roles": item["roles"],
                "template_id": template["template_id"],
                "template_name": template["meal_name"],
                "gap_role": _first_matching_role(item["roles"], relevant_gap_roles),
                "requiredness": _requiredness_from_gap_type(gap_type),
                "message": _gap_message(item=item, gap_type=gap_type),
            }
        )

    return gap_signals[:3]


def _first_matching_role(
    item_roles: list[str],
    relevant_roles: set[str],
) -> str:
    for role in item_roles:
        if role in relevant_roles:
            return role
    return item_roles[0] if item_roles else "unknown"


def _requiredness_from_gap_type(gap_type: str) -> str:
    if gap_type == "low_stock_used":
        return "supporting"
    return "optional"


def _gap_message(*, item: dict[str, Any], gap_type: str) -> str:
    if gap_type == "low_stock_used":
        return f"{item['food_item']} is usable but currently low."
    if gap_type == "low_stock_optional":
        return f"{item['food_item']} may improve this meal but is currently low."
    if gap_type == "out_of_stock_optional":
        return f"{item['food_item']} may improve this meal but is out of stock."
    if gap_type == "expired_optional":
        return f"{item['food_item']} may fit this meal type but is expired and should not be used."
    return f"{item['food_item']} may be a relevant meal gap."


def _build_suggestion_from_match(match: dict[str, Any]) -> dict[str, Any]:
    main_items_used = [item["food_item"] for item in match["main_items"]]
    low_items_used = [
        item["food_item"]
        for item in match["main_items"]
        if item["is_low_stock"]
    ]
    gap_item_names = [gap["food_item"] for gap in match["gap_signals"]]

    reason = _build_reason(match=match)
    restock_hint = _build_restock_hint(match["gap_signals"])

    return {
        "meal_name": match["meal_name"],
        "template_id": match.get("template_id", ""),
        "template_name": match.get("template_name", ""),
        "matched_roles": match.get("matched_roles", []),
        "suggestion_type": match["suggestion_type"],
        "priority": match["priority"],
        "confidence": match["confidence"],
        "main_items_used": main_items_used,
        "use_soon_items_used": match["use_soon_items_used"],
        "low_items_used": low_items_used,
        "missing_or_low_items": gap_item_names,
        "gap_hints": match["gap_signals"],
        "still_possible_without_missing_items": True,
        "reason": reason,
        "restock_hint": restock_hint,
    }


def _build_reason(*, match: dict[str, Any]) -> str:
    main_items = [item["food_item"] for item in match["main_items"]]
    joined_items = ", ".join(main_items)

    if match["use_soon_items_used"]:
        joined_use_soon = ", ".join(match["use_soon_items_used"])
        return (
            f"{match['meal_name']} looks possible using {joined_items}. "
            f"It may be worth prioritising because {joined_use_soon} appears to be use-soon."
        )

    return (
        f"{match['meal_name']} looks possible from available inventory items: "
        f"{joined_items}."
    )


def _build_restock_hint(gap_signals: list[dict[str, Any]]) -> str:
    if not gap_signals:
        return ""

    gap_names = ", ".join(gap["food_item"] for gap in gap_signals)
    return (
        f"{gap_names} may improve this meal, but the suggestion is still possible "
        "without resolving every gap."
    )


def _build_meal_name(
    *,
    template_name: str,
    main_items: list[dict[str, Any]],
) -> str:
    use_soon_items = [item for item in main_items if item["is_use_soon"]]
    protein_items = [item for item in main_items if "protein" in item["roles"]]

    if use_soon_items:
        return f"{use_soon_items[0]['food_item']} {template_name}".strip()

    if protein_items and template_name not in {"Omelette or eggs"}:
        return f"{protein_items[0]['food_item']} {template_name}".strip()

    return template_name


def _score_priority(
    *,
    use_soon_items: list[str],
    main_items: list[dict[str, Any]],
    gap_signals: list[dict[str, Any]],
) -> str:
    if use_soon_items:
        return "high"

    if any(item["is_low_stock"] for item in main_items):
        return "medium"

    if len(main_items) >= 3:
        return "medium"

    if gap_signals:
        return "medium"

    return "low"


def _score_confidence(
    *,
    supporting_count: int,
    main_items: list[dict[str, Any]],
    gap_signals: list[dict[str, Any]],
) -> str:
    unknown_role_count = sum(
        1 for item in main_items if item["roles"] == ["unknown"]
    )
    blocking_gap_count = sum(
        1
        for gap in gap_signals
        if gap["gap_type"] in {"out_of_stock_optional", "expired_optional"}
    )

    if supporting_count >= 2 and unknown_role_count == 0 and blocking_gap_count == 0:
        return "high"

    if supporting_count >= 1 and unknown_role_count <= 1:
        return "medium"

    return "low"


def _deduplicate_suggestions(
    suggestions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    unique: list[dict[str, Any]] = []

    for suggestion in suggestions:
        key = (
            suggestion["meal_name"].lower(),
            tuple(sorted(item.lower() for item in suggestion["main_items_used"])),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(suggestion)

    return unique


def _rank_suggestions(
    suggestions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    priority_score = {"high": 3, "medium": 2, "low": 1}
    confidence_score = {"high": 3, "medium": 2, "low": 1}

    return sorted(
        suggestions,
        key=lambda suggestion: (
            -priority_score.get(suggestion["priority"], 0),
            -confidence_score.get(suggestion["confidence"], 0),
            -len(suggestion["use_soon_items_used"]),
            -len(suggestion["main_items_used"]),
            suggestion["meal_name"].lower(),
        ),
    )


def _inventory_signal_view(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "stock_id": item["stock_id"],
        "food_item": item["food_item"],
        "stock_status": item["stock_status"],
        "availability": item["availability"],
        "is_available": item["is_available"],
        "is_low_stock": item["is_low_stock"],
        "is_use_soon": item["is_use_soon"],
        "days_until_expiry": item["days_until_expiry"],
    }


def _role_signal_view(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "stock_id": item["stock_id"],
        "food_item": item["food_item"],
        "category": item["category"],
        "roles": item["roles"],
    }


def _build_data_quality_signals(
    item_signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []

    for item in item_signals:
        if item["expiry_parse_status"] == "missing":
            signals.append(
                {
                    "signal_type": "missing_expiry_date",
                    "severity": "low",
                    "stock_id": item["stock_id"],
                    "food_item": item["food_item"],
                    "message": "Expiry date is missing. This does not block meal suggestions, but freshness confidence is lower.",
                }
            )

        if item["expiry_parse_status"] == "invalid":
            signals.append(
                {
                    "signal_type": "invalid_expiry_date",
                    "severity": "medium",
                    "stock_id": item["stock_id"],
                    "food_item": item["food_item"],
                    "message": "Expiry date could not be parsed. This does not block meal suggestions, but freshness confidence is lower.",
                }
            )

        if item["roles"] == ["unknown"]:
            signals.append(
                {
                    "signal_type": "unknown_food_role",
                    "severity": "low",
                    "stock_id": item["stock_id"],
                    "food_item": item["food_item"],
                    "message": "Food role could not be confidently inferred from item name or category.",
                }
            )

    return signals


def _normalise_status(value: Any) -> str:
    text = _safe_text(value).lower().replace(" ", "_").replace("-", "_")

    aliases = {
        "verylow": "very_low",
        "very_low_stock": "very_low",
        "low_stock": "low",
        "empty": "out",
        "outofstock": "out",
        "out_of_stock": "out",
        "available": "in_stock",
        "ok": "in_stock",
    }

    return aliases.get(text, text)


def _parse_date_or_status(value: Any) -> tuple[date | None, str]:
    text = _safe_text(value)

    if not text:
        return None, "missing"

    try:
        return datetime.strptime(text, "%Y-%m-%d").date(), "valid"
    except ValueError:
        return None, "invalid"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float_or_none(value: Any) -> float | None:
    text = _safe_text(value)

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _has_positive_amount(value: float | None) -> bool:
    return value is not None and value > 0