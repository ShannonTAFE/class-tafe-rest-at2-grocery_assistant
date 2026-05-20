"""Planning service for Grocery Assistant MCP Version 1.5A.

Version 1.5A introduces a read-only planning layer. It converts existing
inventory and intake records into structured planning signals for the LLM agent.
It must not mutate inventory, intake, consumption, waste, or shopping-list data.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, Callable

from grocery_assistant_mcp.core.grocery_service import list_inventory_items

try:  # Keep this optional so the planning layer can be added before intake APIs stabilize.
    from grocery_assistant_mcp.core.grocery_service import search_intake
except ImportError:  # pragma: no cover - used only if older project versions lack search_intake.
    search_intake = None  # type: ignore[assignment]

from grocery_assistant_mcp.core.planning_helpers import (
    EXPIRY_EXPIRED,
    EXPIRY_INVALID,
    EXPIRY_NO_DATE,
    EXPIRY_USE_SOON,
    UNKNOWN_STOCK_STATUS,
    build_next_action,
    build_safety_metadata,
    build_warning,
    classify_expiry,
    days_until,
    is_usable_stock_status,
    normalize_stock_status,
    normalize_text,
    safe_parse_date,
    severity_rank,
)

VERSION = "1.5A"
LOW_STOCK_REVIEW_VERSION = "1.5B"
LOW_STOCK_REVIEW_SIGNAL_TYPES = {
    "low_stock",
    "very_low_stock",
    "out_of_stock",
}
USE_SOON_REVIEW_VERSION = "1.5B"
USE_SOON_INVENTORY_SIGNAL_TYPES = {
    "use_soon",
    "expired",
}
USE_SOON_DATA_QUALITY_SIGNAL_TYPES = {
    "no_expiry_data",
    "invalid_expiry_date",
}
DATA_QUALITY_REVIEW_VERSION = "1.5B"
DATA_QUALITY_REVIEW_SIGNAL_TYPES = {
    "missing_stock_status",
    "missing_quantity",
    "no_expiry_data",
    "invalid_expiry_date",
}
Signal = dict[str, Any]
Warning = dict[str, Any]


def build_standard_planning_response(
    *,
    tool_name: str,
    summary: str,
    result_type: str = "planning_context",
    status: str = "success",
    inputs: dict[str, Any] | None = None,
    signals: dict[str, list[Signal]] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    warnings: list[Warning] | None = None,
    next_actions: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the stable response shape for all planning tools."""
    return {
        "tool_name": tool_name,
        "summary": summary,
        "result_type": result_type,
        "status": status,
        "inputs": inputs or {},
        "signals": signals
        or {
            "inventory_signals": [],
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": [],
            "system_signals": [],
        },
        "recommendations": recommendations or [],
        "warnings": warnings or [],
        "next_actions": next_actions or [],
        "safety": build_safety_metadata(requires_confirmation=True),
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "version": VERSION,
            "records_checked": {
                "inventory": 0,
                "intake_history": 0,
                "intake_items": 0,
                "consumption": 0,
                "waste": 0,
            },
            **(metadata or {}),
        },
    }


def build_planning_context(
    *,
    recent_days: int = 7,
    include_inventory: bool = True,
    include_recent_intake: bool = True,
    include_consumption: bool = False,
    include_waste: bool = False,
    today: date | None = None,
) -> dict[str, Any]:
    """Build a read-only planning context from current grocery records."""
    reference_date = today or date.today()
    recent_days = _coerce_recent_days(recent_days)

    signals: dict[str, list[Signal]] = {
        "inventory_signals": [],
        "intake_signals": [],
        "consumption_signals": [],
        "waste_signals": [],
        "data_quality_signals": [],
        "system_signals": [],
    }
    warnings: list[Warning] = []
    next_actions: list[dict[str, Any]] = []
    records_checked = {
        "inventory": 0,
        "intake_history": 0,
        "intake_items": 0,
        "consumption": 0,
        "waste": 0,
    }

    if include_inventory:
        inventory_records = list_inventory_items()
        records_checked["inventory"] = len(inventory_records)
        inventory_result = build_inventory_planning_signals(
            inventory_records,
            today=reference_date,
        )
        signals["inventory_signals"].extend(inventory_result["inventory_signals"])
        signals["data_quality_signals"].extend(inventory_result["data_quality_signals"])
        warnings.extend(inventory_result["warnings"])

    if include_recent_intake:
        intake_result = build_intake_planning_signals(
            recent_days=recent_days,
            today=reference_date,
        )
        signals["intake_signals"].extend(intake_result["intake_signals"])
        signals["data_quality_signals"].extend(intake_result["data_quality_signals"])
        warnings.extend(intake_result["warnings"])
        records_checked["intake_history"] = intake_result["records_checked"].get(
            "intake_history", 0
        )
        records_checked["intake_items"] = intake_result["records_checked"].get(
            "intake_items", 0
        )

    if include_consumption:
        warnings.append(
            build_warning(
                warning_type="consumption_not_yet_implemented",
                severity="low",
                message="Consumption planning signals are reserved for a later Version 1.5 stage.",
                agent_guidance="Do not claim consumption-pattern learning from this planning context yet.",
            )
        )

    if include_waste:
        warnings.append(
            build_warning(
                warning_type="waste_not_yet_implemented",
                severity="low",
                message="Waste planning signals are reserved for a later Version 1.5 stage.",
                agent_guidance="Do not claim waste-pattern learning from this planning context yet.",
            )
        )

    next_actions.extend(_build_default_next_actions())

    total_signals = sum(len(signal_list) for signal_list in signals.values())
    summary = (
        f"Planning context prepared with {total_signals} signal(s). "
        "No records were changed."
    )

    return build_standard_planning_response(
        tool_name="review_planning_context",
        summary=summary,
        result_type="planning_context",
        inputs={
            "recent_days": recent_days,
            "include_inventory": include_inventory,
            "include_recent_intake": include_recent_intake,
            "include_consumption": include_consumption,
            "include_waste": include_waste,
        },
        signals=signals,
        warnings=_sort_warnings(warnings),
        next_actions=next_actions,
        metadata={
            "records_checked": records_checked,
            "reference_date": reference_date.isoformat(),
        },
    )


def review_low_stock_items(
    *,
    include_low: bool = True,
    include_very_low: bool = True,
    include_out: bool = True,
    today: date | None = None,
) -> dict[str, Any]:
    """
    Return a focused read-only review of low, very-low, and out-of-stock items.

    Version 1.5B-A scope:
    - reuse Version 1.5A inventory planning signals
    - filter only stock-attention signals
    - keep recommendations empty
    - do not update inventory, create shopping-list records, or deduct stock
    """
    included_signal_types = _selected_low_stock_signal_types(
        include_low=include_low,
        include_very_low=include_very_low,
        include_out=include_out,
    )

    planning_context = build_planning_context(
        recent_days=1,
        include_inventory=True,
        include_recent_intake=False,
        include_consumption=False,
        include_waste=False,
        today=today,
    )

    source_signals = planning_context.get("signals", {})
    inventory_signals = source_signals.get("inventory_signals", [])

    low_stock_signals = [
        signal
        for signal in inventory_signals
        if signal.get("signal_type") in included_signal_types
    ]

    warnings = list(planning_context.get("warnings", []))

    if not included_signal_types:
        warnings.append(
            build_warning(
                warning_type="no_low_stock_filters_selected",
                severity="low",
                message="No low-stock signal filters were selected.",
                agent_guidance=(
                    "Ask the user which stock attention states they want to review, "
                    "or call the tool again with at least one include flag enabled."
                ),
            )
        )
    elif not low_stock_signals:
        warnings.append(
            build_warning(
                warning_type="no_low_stock_items",
                severity="low",
                message=(
                    "No low, very-low, or out-of-stock inventory signals were found "
                    "for the selected filters."
                ),
                agent_guidance=(
                    "Do not tell the user they need to restock items unless another "
                    "source of evidence supports that claim."
                ),
            )
        )

    next_actions = [
        build_next_action(
            action_type="review_planning_context",
            label="Review full planning context",
            tool_name="review_planning_context",
            requires_confirmation=False,
            reason=(
                "Use this if the agent needs broader inventory and recent-intake "
                "context before making suggestions."
            ),
        ),
        build_next_action(
            action_type="update_inventory",
            label="Update an inventory item",
            tool_name="update_inventory_item",
            requires_confirmation=True,
            reason=(
                "Use only after the user explicitly confirms a stock, quantity, "
                "expiry, or note change."
            ),
        ),
    ]

    records_checked = planning_context.get("metadata", {}).get(
        "records_checked",
        {
            "inventory": 0,
            "intake_history": 0,
            "intake_items": 0,
            "consumption": 0,
            "waste": 0,
        },
    )

    reference_date = planning_context.get("metadata", {}).get(
        "reference_date",
        (today or date.today()).isoformat(),
    )

    summary = (
        "Low-stock inventory review prepared with "
        f"{len(low_stock_signals)} attention signal(s). No records were changed."
    )

    return build_standard_planning_response(
        tool_name="review_low_stock_items",
        summary=summary,
        result_type="inventory_low_stock_review",
        inputs={
            "include_low": include_low,
            "include_very_low": include_very_low,
            "include_out": include_out,
        },
        signals={
            "inventory_signals": low_stock_signals,
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": [],
            "system_signals": [],
        },
        recommendations=[],
        warnings=_sort_warnings(warnings),
        next_actions=next_actions,
        metadata={
            "version": LOW_STOCK_REVIEW_VERSION,
            "records_checked": records_checked,
            "reference_date": reference_date,
            "source_tool": "review_planning_context",
            "filtered_signal_types": sorted(included_signal_types),
            "selected_signal_count": len(low_stock_signals),
        },
    )


def review_use_soon_items(
    *,
    include_use_soon: bool = True,
    include_expired: bool = True,
    include_no_expiry_data: bool = True,
    include_invalid_expiry_date: bool = True,
    today: date | None = None,
) -> dict[str, Any]:
    """
    Return a focused read-only review of expiry and use-soon inventory signals.

    Version 1.5B-B scope:
    - reuse Version 1.5A inventory planning signals
    - filter expiry-related inventory and data-quality signals
    - keep recommendations empty
    - do not update inventory, create waste records, or deduct stock
    """
    selected_inventory_signal_types = _selected_use_soon_inventory_signal_types(
        include_use_soon=include_use_soon,
        include_expired=include_expired,
    )
    selected_data_quality_signal_types = _selected_use_soon_data_quality_signal_types(
        include_no_expiry_data=include_no_expiry_data,
        include_invalid_expiry_date=include_invalid_expiry_date,
    )

    planning_context = build_planning_context(
        recent_days=1,
        include_inventory=True,
        include_recent_intake=False,
        include_consumption=False,
        include_waste=False,
        today=today,
    )

    source_signals = planning_context.get("signals", {})
    inventory_signals = source_signals.get("inventory_signals", [])
    data_quality_signals = source_signals.get("data_quality_signals", [])

    use_soon_inventory_signals = [
        signal
        for signal in inventory_signals
        if signal.get("signal_type") in selected_inventory_signal_types
    ]
    use_soon_data_quality_signals = [
        signal
        for signal in data_quality_signals
        if signal.get("signal_type") in selected_data_quality_signal_types
    ]

    selected_signal_count = len(use_soon_inventory_signals) + len(
        use_soon_data_quality_signals
    )
    selected_signal_types = (
        selected_inventory_signal_types | selected_data_quality_signal_types
    )

    warnings = list(planning_context.get("warnings", []))

    if not selected_signal_types:
        warnings.append(
            build_warning(
                warning_type="no_use_soon_filters_selected",
                severity="low",
                message="No use-soon or expiry signal filters were selected.",
                agent_guidance=(
                    "Ask the user which expiry states they want to review, or call "
                    "the tool again with at least one include flag enabled."
                ),
            )
        )
    elif selected_signal_count == 0:
        warnings.append(
            build_warning(
                warning_type="no_use_soon_items",
                severity="low",
                message=(
                    "No use-soon, expired, missing-expiry, or invalid-expiry "
                    "inventory signals were found for the selected filters."
                ),
                agent_guidance=(
                    "Do not tell the user they have expiry-priority items unless "
                    "another source of evidence supports that claim."
                ),
            )
        )

    next_actions = [
        build_next_action(
            action_type="review_planning_context",
            label="Review full planning context",
            tool_name="review_planning_context",
            requires_confirmation=False,
            reason=(
                "Use this if the agent needs broader inventory and recent-intake "
                "context before making suggestions."
            ),
        ),
        build_next_action(
            action_type="review_low_stock",
            label="Review low and very-low stock items",
            tool_name="review_low_stock_items",
            requires_confirmation=False,
            reason=(
                "Use this if the agent needs stock-attention context before "
                "making restock or careful-use suggestions."
            ),
        ),
        build_next_action(
            action_type="update_inventory",
            label="Update an inventory item",
            tool_name="update_inventory_item",
            requires_confirmation=True,
            reason=(
                "Use only after the user explicitly confirms a stock, quantity, "
                "expiry, or note change."
            ),
        ),
        build_next_action(
            action_type="remove_inventory_item",
            label="Remove an expired or incorrect inventory item",
            tool_name="remove_inventory_item",
            requires_confirmation=True,
            reason=(
                "Use only after the user explicitly confirms that an item should "
                "be removed from inventory. Waste-related removals may also create "
                "a waste record."
            ),
        ),
    ]

    records_checked = planning_context.get("metadata", {}).get(
        "records_checked",
        {
            "inventory": 0,
            "intake_history": 0,
            "intake_items": 0,
            "consumption": 0,
            "waste": 0,
        },
    )

    reference_date = planning_context.get("metadata", {}).get(
        "reference_date",
        (today or date.today()).isoformat(),
    )

    summary = (
        "Use-soon inventory review prepared with "
        f"{selected_signal_count} expiry-related signal(s). No records were changed."
    )

    return build_standard_planning_response(
        tool_name="review_use_soon_items",
        summary=summary,
        result_type="inventory_use_soon_review",
        inputs={
            "include_use_soon": include_use_soon,
            "include_expired": include_expired,
            "include_no_expiry_data": include_no_expiry_data,
            "include_invalid_expiry_date": include_invalid_expiry_date,
        },
        signals={
            "inventory_signals": use_soon_inventory_signals,
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": use_soon_data_quality_signals,
            "system_signals": [],
        },
        recommendations=[],
        warnings=_sort_warnings(warnings),
        next_actions=next_actions,
        metadata={
            "version": USE_SOON_REVIEW_VERSION,
            "records_checked": records_checked,
            "reference_date": reference_date,
            "source_tool": "review_planning_context",
            "filtered_inventory_signal_types": sorted(selected_inventory_signal_types),
            "filtered_data_quality_signal_types": sorted(selected_data_quality_signal_types),
            "selected_signal_count": selected_signal_count,
        },
    )


def review_inventory_data_quality(
    *,
    include_missing_stock_status: bool = True,
    include_missing_quantity: bool = True,
    include_no_expiry_data: bool = True,
    include_invalid_expiry_date: bool = True,
    today: date | None = None,
) -> dict[str, Any]:
    """
    Return a focused read-only review of inventory data-quality signals.

    Version 1.5B-C scope:
    - reuse Version 1.5A inventory data-quality signals
    - focus on missing or weak inventory fields
    - keep recommendations empty
    - do not update inventory or infer corrections automatically
    """
    selected_signal_types = _selected_inventory_data_quality_signal_types(
        include_missing_stock_status=include_missing_stock_status,
        include_missing_quantity=include_missing_quantity,
        include_no_expiry_data=include_no_expiry_data,
        include_invalid_expiry_date=include_invalid_expiry_date,
    )

    planning_context = build_planning_context(
        recent_days=1,
        include_inventory=True,
        include_recent_intake=False,
        include_consumption=False,
        include_waste=False,
        today=today,
    )

    source_signals = planning_context.get("signals", {})
    data_quality_signals = source_signals.get("data_quality_signals", [])

    selected_data_quality_signals = [
        signal
        for signal in data_quality_signals
        if signal.get("domain") == "data_quality"
        and signal.get("signal_type") in selected_signal_types
    ]

    warnings = list(planning_context.get("warnings", []))

    if not selected_signal_types:
        warnings.append(
            build_warning(
                warning_type="no_data_quality_filters_selected",
                severity="low",
                message="No inventory data-quality signal filters were selected.",
                agent_guidance=(
                    "Ask the user which data-quality states they want to review, "
                    "or call the tool again with at least one include flag enabled."
                ),
            )
        )
    elif not selected_data_quality_signals:
        warnings.append(
            build_warning(
                warning_type="no_inventory_data_quality_issues",
                severity="low",
                message=(
                    "No selected inventory data-quality issues were found. "
                    "This does not prove all inventory data is perfect; it only means "
                    "the selected signal checks did not find issues."
                ),
                agent_guidance=(
                    "Do not overclaim that the inventory is fully clean. You may say "
                    "no selected data-quality issues were found."
                ),
            )
        )

    next_actions = [
        build_next_action(
            action_type="review_planning_context",
            label="Review full planning context",
            tool_name="review_planning_context",
            requires_confirmation=False,
            reason=(
                "Use this if the agent needs broader inventory and recent-intake "
                "context before making suggestions."
            ),
        ),
        build_next_action(
            action_type="review_low_stock",
            label="Review low and very-low stock items",
            tool_name="review_low_stock_items",
            requires_confirmation=False,
            reason=(
                "Use this if the agent needs stock-attention context before "
                "making restock or careful-use suggestions."
            ),
        ),
        build_next_action(
            action_type="review_use_soon",
            label="Review expiring and missing-expiry inventory items",
            tool_name="review_use_soon_items",
            requires_confirmation=False,
            reason=(
                "Use this if the agent needs expiry-related context before "
                "making use-soon or waste-reduction suggestions."
            ),
        ),
        build_next_action(
            action_type="update_inventory",
            label="Update an inventory item",
            tool_name="update_inventory_item",
            requires_confirmation=True,
            reason=(
                "Use only after the user explicitly confirms a stock, quantity, "
                "expiry, or note change."
            ),
        ),
    ]

    records_checked = planning_context.get("metadata", {}).get(
        "records_checked",
        {
            "inventory": 0,
            "intake_history": 0,
            "intake_items": 0,
            "consumption": 0,
            "waste": 0,
        },
    )

    reference_date = planning_context.get("metadata", {}).get(
        "reference_date",
        (today or date.today()).isoformat(),
    )

    summary = (
        "Inventory data-quality review prepared with "
        f"{len(selected_data_quality_signals)} issue signal(s). No records were changed."
    )

    return build_standard_planning_response(
        tool_name="review_inventory_data_quality",
        summary=summary,
        result_type="inventory_data_quality_review",
        inputs={
            "include_missing_stock_status": include_missing_stock_status,
            "include_missing_quantity": include_missing_quantity,
            "include_no_expiry_data": include_no_expiry_data,
            "include_invalid_expiry_date": include_invalid_expiry_date,
        },
        signals={
            "inventory_signals": [],
            "intake_signals": [],
            "consumption_signals": [],
            "waste_signals": [],
            "data_quality_signals": selected_data_quality_signals,
            "system_signals": [],
        },
        recommendations=[],
        warnings=_sort_warnings(warnings),
        next_actions=next_actions,
        metadata={
            "version": DATA_QUALITY_REVIEW_VERSION,
            "records_checked": records_checked,
            "reference_date": reference_date,
            "source_tool": "review_planning_context",
            "filtered_data_quality_signal_types": sorted(selected_signal_types),
            "selected_signal_count": len(selected_data_quality_signals),
        },
    )


def build_inventory_planning_signals(
    inventory_records: list[dict[str, Any]],
    *,
    today: date | None = None,
    use_soon_days: int = 7,
) -> dict[str, Any]:
    """Convert inventory rows into planning and data-quality signals."""
    reference_date = today or date.today()
    inventory_signals: list[Signal] = []
    data_quality_signals: list[Signal] = []
    warnings: list[Warning] = []

    if not inventory_records:
        warnings.append(
            build_warning(
                warning_type="missing_inventory_data",
                severity="high",
                message="No inventory records were found.",
                agent_guidance="Avoid making inventory-based meal or restock claims.",
            )
        )
        return {
            "inventory_signals": inventory_signals,
            "data_quality_signals": data_quality_signals,
            "warnings": warnings,
        }

    for index, record in enumerate(inventory_records, start=1):
        stock_status = normalize_stock_status(record.get("stock_status", ""))
        expiry_state = classify_expiry(
            record.get("expiry_date", ""),
            today=reference_date,
            use_soon_days=use_soon_days,
        )
        parsed_expiry = safe_parse_date(record.get("expiry_date", ""))
        days_to_expiry = days_until(parsed_expiry, today=reference_date)

        if stock_status == UNKNOWN_STOCK_STATUS:
            data_quality_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="missing_stock_status",
                    severity="medium",
                    polarity="caution",
                    confidence="high",
                    reason="Stock status is blank or not recognised.",
                    source_fields=["stock_status"],
                    agent_guidance="Treat this item cautiously until the user confirms the stock status.",
                    limitations=["Do not use this item as strong evidence of availability."],
                    domain="data_quality",
                )
            )

        if _is_missing_number(record.get("quantity")) and _is_missing_number(
            record.get("servings_remaining")
        ):
            data_quality_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="missing_quantity",
                    severity="low",
                    polarity="caution",
                    confidence="high",
                    reason="Both quantity and servings_remaining are blank or unavailable.",
                    source_fields=["quantity", "servings_remaining"],
                    agent_guidance="Avoid making precise portion or serving claims for this item.",
                    limitations=["Do not calculate exact meals remaining from this item."],
                    domain="data_quality",
                )
            )

        if expiry_state == EXPIRY_INVALID:
            data_quality_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="invalid_expiry_date",
                    severity="medium",
                    polarity="caution",
                    confidence="high",
                    reason="Expiry date could not be parsed.",
                    source_fields=["expiry_date"],
                    agent_guidance="Do not make expiry-based claims for this item.",
                    limitations=["Expiry timing is unknown until corrected."],
                    domain="data_quality",
                )
            )

        if stock_status == "expired" or expiry_state == EXPIRY_EXPIRED:
            inventory_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="expired",
                    severity="critical",
                    polarity="negative",
                    confidence="high",
                    reason="Item is marked expired or has an expiry date in the past.",
                    source_fields=["stock_status", "expiry_date"],
                    agent_guidance="Exclude this item from meal suggestions unless the user confirms it is safe.",
                    limitations=["Do not suggest consuming this item as available food."],
                    extra={"expiry_state": expiry_state, "days_until_expiry": days_to_expiry},
                )
            )
            continue

        if stock_status == "out":
            inventory_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="out_of_stock",
                    severity="high",
                    polarity="negative",
                    confidence="high",
                    reason="Item is marked out of stock.",
                    source_fields=["stock_status"],
                    agent_guidance="Do not count this as an available ingredient; it may still inform restock planning later.",
                    limitations=["Do not use this item in available-inventory meal suggestions."],
                )
            )
            continue

        if is_usable_stock_status(stock_status):
            inventory_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="available_inventory",
                    severity="low",
                    polarity="positive",
                    confidence="medium" if stock_status == UNKNOWN_STOCK_STATUS else "high",
                    reason="Item appears usable based on stock status and expiry information.",
                    source_fields=["stock_status", "expiry_date"],
                    agent_guidance="This item can support soft meal-planning suggestions.",
                    limitations=["Do not deduct inventory unless the user explicitly confirms a write action."],
                    extra={"expiry_state": expiry_state, "days_until_expiry": days_to_expiry},
                )
            )

        if stock_status == "low":
            inventory_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="low_stock",
                    severity="medium",
                    polarity="caution",
                    confidence="high",
                    reason="Item is marked low.",
                    source_fields=["stock_status"],
                    agent_guidance="Mention as a possible restock or careful-use item.",
                    limitations=["Do not automatically add this item to a shopping list."],
                )
            )

        if stock_status == "very_low":
            inventory_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="very_low_stock",
                    severity="high",
                    polarity="caution",
                    confidence="high",
                    reason="Item is marked very low.",
                    source_fields=["stock_status"],
                    agent_guidance="Prioritise this as an attention item for restock or careful planning.",
                    limitations=["Do not automatically add this item to a shopping list."],
                )
            )

        if expiry_state == EXPIRY_USE_SOON and is_usable_stock_status(stock_status):
            inventory_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="use_soon",
                    severity="medium" if (days_to_expiry or 0) > 2 else "high",
                    polarity="caution",
                    confidence="high",
                    reason="Item is available and expires within the use-soon window.",
                    source_fields=["stock_status", "expiry_date"],
                    agent_guidance="Prioritise this item in meal suggestions if the user wants to reduce waste.",
                    limitations=["Do not imply the item has already been used or consumed."],
                    extra={"expiry_state": expiry_state, "days_until_expiry": days_to_expiry},
                )
            )

        if expiry_state == EXPIRY_NO_DATE:
            data_quality_signals.append(
                _inventory_signal(
                    index=index,
                    record=record,
                    signal_type="no_expiry_data",
                    severity="low",
                    polarity="neutral",
                    confidence="high",
                    reason="No expiry date is available for this item.",
                    source_fields=["expiry_date"],
                    agent_guidance="Avoid expiry-based prioritisation for this item.",
                    limitations=["Cannot determine use-soon or expired status from date."],
                    domain="data_quality",
                )
            )

    if not any(signal["signal_type"] == "available_inventory" for signal in inventory_signals):
        warnings.append(
            build_warning(
                warning_type="no_available_inventory",
                severity="high",
                message="No clearly available inventory items were found.",
                agent_guidance="Avoid suggesting meals based on current inventory unless the user provides more context.",
            )
        )

    if any(signal["signal_type"] == "expired" for signal in inventory_signals):
        warnings.append(
            build_warning(
                warning_type="expired_items_excluded",
                severity="high",
                message="Expired items were identified and should be excluded from meal suggestions.",
                agent_guidance="Warn the user before considering any expired item as usable.",
            )
        )

    return {
        "inventory_signals": sorted(
            inventory_signals,
            key=lambda signal: severity_rank(signal.get("severity", "none")),
            reverse=True,
        ),
        "data_quality_signals": data_quality_signals,
        "warnings": warnings,
    }


def build_intake_planning_signals(
    *,
    recent_days: int = 7,
    today: date | None = None,
) -> dict[str, Any]:
    """Build basic recent-intake planning signals when search_intake is available."""
    reference_date = today or date.today()
    recent_days = _coerce_recent_days(recent_days)
    intake_signals: list[Signal] = []
    data_quality_signals: list[Signal] = []
    warnings: list[Warning] = []
    records_checked = {"intake_history": 0, "intake_items": 0}

    if search_intake is None:
        warnings.append(
            build_warning(
                warning_type="intake_search_unavailable",
                severity="medium",
                message="The search_intake function is not available in this project version.",
                agent_guidance="Do not make claims about recent intake from this planning context.",
            )
        )
        return {
            "intake_signals": intake_signals,
            "data_quality_signals": data_quality_signals,
            "warnings": warnings,
            "records_checked": records_checked,
        }

    raw_result = _call_search_intake(search_intake)
    entries = _extract_intake_entries(raw_result)
    items = _extract_intake_items(raw_result)
    records_checked["intake_history"] = len(entries)
    records_checked["intake_items"] = len(items)

    cutoff_date = reference_date - timedelta(days=recent_days - 1)
    recent_entries = [
        entry
        for entry in entries
        if _entry_in_recent_window(entry, cutoff_date=cutoff_date, today=reference_date)
    ]

    if not recent_entries:
        warnings.append(
            build_warning(
                warning_type="no_recent_intake_records",
                severity="medium",
                message=f"No intake records were found in the last {recent_days} day(s).",
                agent_guidance="Avoid claiming that meal suggestions avoid recent repetition.",
            )
        )
        return {
            "intake_signals": intake_signals,
            "data_quality_signals": data_quality_signals,
            "warnings": warnings,
            "records_checked": records_checked,
        }

    for index, entry in enumerate(recent_entries[:20], start=1):
        meal_name = normalize_text(entry.get("meal_name", "")) or "Unnamed meal"
        intake_signals.append(
            {
                "signal_id": f"sig_intake_{index:03d}_recently_eaten",
                "domain": "intake",
                "signal_type": "recently_eaten",
                "subject": {
                    "intake_id": normalize_text(entry.get("intake_id", "")),
                    "meal_name": meal_name,
                    "meal_type": normalize_text(entry.get("meal_type", "")),
                    "date": normalize_text(entry.get("date", "")),
                },
                "severity": "low",
                "polarity": "neutral",
                "confidence": "high",
                "reason": "Meal appears in the recent intake window.",
                "evidence": {
                    "source": "user_intake_history.csv",
                    "evidence_type": "observed",
                    "source_fields": ["date", "meal_name", "meal_type"],
                    "source_values": {
                        "date": normalize_text(entry.get("date", "")),
                        "meal_name": meal_name,
                        "meal_type": normalize_text(entry.get("meal_type", "")),
                    },
                },
                "data_quality": {
                    "quality_level": "partial" if not entry.get("meal_name") else "complete",
                    "missing_fields": [
                        field
                        for field in ("meal_name", "meal_type", "date")
                        if not normalize_text(entry.get(field, ""))
                    ],
                    "inference_required": False,
                },
                "agent_guidance": "Use this to avoid repeating recent meals when making future suggestions.",
                "limitations": [
                    "Do not infer user preference from one recent intake record alone.",
                    "Do not mutate intake records from this signal.",
                ],
            }
        )

    return {
        "intake_signals": intake_signals,
        "data_quality_signals": data_quality_signals,
        "warnings": warnings,
        "records_checked": records_checked,
    }


def _inventory_signal(
    *,
    index: int,
    record: dict[str, Any],
    signal_type: str,
    severity: str,
    polarity: str,
    confidence: str,
    reason: str,
    source_fields: list[str],
    agent_guidance: str,
    limitations: list[str],
    domain: str = "inventory",
    extra: dict[str, Any] | None = None,
) -> Signal:
    source_values = {field: record.get(field, "") for field in source_fields}
    missing_fields = [field for field in source_fields if not normalize_text(record.get(field, ""))]

    return {
        "signal_id": f"sig_{domain}_{index:03d}_{signal_type}",
        "domain": domain,
        "signal_type": signal_type,
        "subject": {
            "stock_id": normalize_text(record.get("stock_id", "")),
            "food_item": normalize_text(record.get("food_item", "")),
            "brand": normalize_text(record.get("brand", "")),
            "category": normalize_text(record.get("category", "")),
            "location": normalize_text(record.get("location", "")),
        },
        "severity": severity,
        "polarity": polarity,
        "confidence": confidence,
        "reason": reason,
        "evidence": {
            "source": "user_inventory.csv",
            "evidence_type": "observed",
            "source_fields": source_fields,
            "source_values": source_values,
        },
        "data_quality": {
            "quality_level": "partial" if missing_fields else "complete",
            "missing_fields": missing_fields,
            "conflicting_fields": [],
            "inference_required": False,
        },
        "agent_guidance": agent_guidance,
        "limitations": limitations,
        **(extra or {}),
    }


def _is_missing_number(value: Any) -> bool:
    text = normalize_text(value)
    if not text:
        return True
    try:
        return float(text) == 0.0
    except ValueError:
        return True


def _coerce_recent_days(recent_days: int) -> int:
    try:
        value = int(recent_days)
    except (TypeError, ValueError):
        return 7
    return min(max(value, 1), 90)


def _sort_warnings(warnings: list[Warning]) -> list[Warning]:
    return sorted(
        warnings,
        key=lambda warning: severity_rank(warning.get("severity", "none")),
        reverse=True,
    )


def _selected_low_stock_signal_types(
    *,
    include_low: bool,
    include_very_low: bool,
    include_out: bool,
) -> set[str]:
    """Return the low-stock signal types selected by the review flags."""
    selected: set[str] = set()

    if include_low:
        selected.add("low_stock")

    if include_very_low:
        selected.add("very_low_stock")

    if include_out:
        selected.add("out_of_stock")

    return selected


def _selected_use_soon_inventory_signal_types(
    *,
    include_use_soon: bool,
    include_expired: bool,
) -> set[str]:
    """Return the expiry-related inventory signal types selected by flags."""
    selected: set[str] = set()

    if include_use_soon:
        selected.add("use_soon")

    if include_expired:
        selected.add("expired")

    return selected


def _selected_use_soon_data_quality_signal_types(
    *,
    include_no_expiry_data: bool,
    include_invalid_expiry_date: bool,
) -> set[str]:
    """Return the expiry-related data-quality signal types selected by flags."""
    selected: set[str] = set()

    if include_no_expiry_data:
        selected.add("no_expiry_data")

    if include_invalid_expiry_date:
        selected.add("invalid_expiry_date")

    return selected


def _selected_inventory_data_quality_signal_types(
    *,
    include_missing_stock_status: bool,
    include_missing_quantity: bool,
    include_no_expiry_data: bool,
    include_invalid_expiry_date: bool,
) -> set[str]:
    """Return the inventory data-quality signal types selected by flags."""
    selected: set[str] = set()

    if include_missing_stock_status:
        selected.add("missing_stock_status")

    if include_missing_quantity:
        selected.add("missing_quantity")

    if include_no_expiry_data:
        selected.add("no_expiry_data")

    if include_invalid_expiry_date:
        selected.add("invalid_expiry_date")

    return selected


def _build_default_next_actions() -> list[dict[str, Any]]:
    return [
        build_next_action(
            action_type="review_low_stock",
            label="Review low and very-low stock items",
            tool_name="review_low_stock_items",
            requires_confirmation=False,
            reason="This keeps the interaction read-only and helps inspect attention items.",
        ),
        build_next_action(
            action_type="review_use_soon",
            label="Review expiring and missing-expiry inventory items",
            tool_name="review_use_soon_items",
            requires_confirmation=False,
            reason="This keeps the interaction read-only and helps inspect expiry-related attention items.",
        ),
        build_next_action(
            action_type="review_inventory_data_quality",
            label="Review inventory data-quality issues",
            tool_name="review_inventory_data_quality",
            requires_confirmation=False,
            reason="This keeps the interaction read-only and helps inspect missing or weak inventory fields.",
        ),
        build_next_action(
            action_type="log_with_inventory_items",
            label="Log a meal with inventory deductions",
            tool_name="add_meal_with_inventory_items",
            requires_confirmation=True,
            reason="Use only after the user explicitly confirms they want to log intake and deduct inventory.",
        ),
        build_next_action(
            action_type="update_inventory",
            label="Update an inventory item",
            tool_name="update_inventory_item",
            requires_confirmation=True,
            reason="Use only after the user explicitly confirms a stock, quantity, expiry, or note change.",
        ),
    ]


def _call_search_intake(search_func: Callable[..., Any]) -> Any:
    try:
        return search_func(query="", date="")
    except TypeError:
        return search_func()


def _extract_intake_entries(raw_result: Any) -> list[dict[str, Any]]:
    if isinstance(raw_result, dict):
        entries = raw_result.get("matching_entries", [])
        return entries if isinstance(entries, list) else []
    if isinstance(raw_result, list):
        return raw_result
    return []


def _extract_intake_items(raw_result: Any) -> list[dict[str, Any]]:
    if isinstance(raw_result, dict):
        items = raw_result.get("matching_items", [])
        return items if isinstance(items, list) else []
    return []


def _entry_in_recent_window(
    entry: dict[str, Any],
    *,
    cutoff_date: date,
    today: date,
) -> bool:
    entry_date = safe_parse_date(entry.get("date", ""))
    if entry_date is None:
        return False
    return cutoff_date <= entry_date <= today
