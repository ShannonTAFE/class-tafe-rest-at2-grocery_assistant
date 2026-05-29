"""Shared MCP tool allowlist and safety policy."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# Safe read/search/review/draft tools for normal agent testing.
READ_REVIEW_DRAFT_TOOLS: set[str] = {
    # Inventory reads
    "search_inventory",

    # Intake reads
    "get_recent_intake",
    "get_daily_intake_summary",
    "search_intake",

    # Planning / recommendations
    "review_planning_context",
    "review_low_stock_items",
    "review_use_soon_items",
    "review_inventory_data_quality",
    "draft_restock_suggestions_tool",
    "draft_meal_suggestions_tool",
}

# Tools that mutate records or log events. Hidden unless writes are explicitly enabled.
WRITE_TOOLS: set[str] = {
    # Inventory writes
    "add_inventory_item",
    "update_inventory_item",
    "remove_inventory_item",
    "consume_inventory_item",

    # Intake writes
    "add_intake_entry",
    "add_intake_item",
    "update_intake_entry",
    "update_intake_item",
    "remove_intake_entry",
    "remove_intake_item",

    # Inventory-linked / batch workflows
    "add_intake_item_from_inventory",
    "add_meal_with_items",
    "add_meal_with_inventory_items",
}

DESTRUCTIVE_TOOLS: set[str] = {
    "remove_inventory_item",
    "remove_intake_entry",
    "remove_intake_item",
}

KNOWN_TOOLS: set[str] = READ_REVIEW_DRAFT_TOOLS | WRITE_TOOLS

DEFAULT_TOOL_ARGS: dict[str, dict[str, Any]] = {
    "search_inventory": {"query": "", "category": "", "location": ""},
    "get_recent_intake": {"limit": 10},
    "get_daily_intake_summary": {"date": ""},
    "search_intake": {"query": "", "date": ""},
    "review_use_soon_items": {
        "include_use_soon": True,
        "include_expired": True,
        "include_no_expiry_data": True,
        "include_invalid_expiry_date": True,
    },
}


def allowed_tool_names(*, allow_writes: bool) -> set[str]:
    """Return the effective allowlist for the current run."""

    if allow_writes:
        return set(KNOWN_TOOLS)
    return set(READ_REVIEW_DRAFT_TOOLS)


def is_write_tool(tool_name: str) -> bool:
    return tool_name in WRITE_TOOLS


def is_destructive_tool(tool_name: str) -> bool:
    return tool_name in DESTRUCTIVE_TOOLS


def is_tool_allowed(tool_name: str, *, allow_writes: bool) -> bool:
    return tool_name in allowed_tool_names(allow_writes=allow_writes)


def filter_tool_names(tool_names: Iterable[str], *, allow_writes: bool) -> list[str]:
    """Preserve server order while applying the client allowlist."""

    allowed = allowed_tool_names(allow_writes=allow_writes)
    return [name for name in tool_names if name in allowed]


def merge_default_args(tool_name: str, args: dict[str, Any] | None) -> dict[str, Any]:
    """Fill known defaults for tools whose MCP schemas expect explicit optional fields."""

    merged = dict(DEFAULT_TOOL_ARGS.get(tool_name, {}))
    if args:
        merged.update(args)
    return merged
