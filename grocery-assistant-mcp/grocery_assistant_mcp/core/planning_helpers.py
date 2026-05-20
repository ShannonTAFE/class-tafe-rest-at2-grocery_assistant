"""Planning helper functions for Grocery Assistant MCP Version 1.5A.

These helpers convert raw grocery records into safe, structured planning
signals. They are intentionally read-only and should not perform any CSV writes.
"""

from __future__ import annotations

from datetime import date, datetime
from math import isnan
from typing import Any

ATTENTION_STOCK_STATUSES = {"low", "very_low", "out", "expired"}
USABLE_STOCK_STATUSES = {"in_stock", "low", "very_low"}
NON_USABLE_STOCK_STATUSES = {"out", "expired"}
LOW_STOCK_STATUSES = {"low", "very_low"}
UNKNOWN_STOCK_STATUS = "unknown"

STATUS_ALIASES = {
    "": UNKNOWN_STOCK_STATUS,
    "none": UNKNOWN_STOCK_STATUS,
    "nan": UNKNOWN_STOCK_STATUS,
    "ok": "in_stock",
    "available": "in_stock",
    "stocked": "in_stock",
    "in stock": "in_stock",
    "instock": "in_stock",
    "very low": "very_low",
    "very-low": "very_low",
    "almost out": "very_low",
    "empty": "out",
    "out of stock": "out",
    "out-of-stock": "out",
    "used up": "out",
}

EXPIRY_EXPIRED = "expired"
EXPIRY_USE_SOON = "use_soon"
EXPIRY_FUTURE = "future"
EXPIRY_NO_DATE = "no_expiry_date"
EXPIRY_INVALID = "invalid_expiry_date"

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def normalize_text(value: Any) -> str:
    """Return a stripped string, treating None/NaN-like values as blank."""
    if value is None:
        return ""

    if isinstance(value, float):
        try:
            if isnan(value):
                return ""
        except TypeError:
            pass

    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def normalize_stock_status(value: Any) -> str:
    """Normalize inventory stock status into the project's planning vocabulary."""
    text = normalize_text(value).lower().replace("-", "_").replace(" ", "_")
    if text in {"", "none", "nan", "null"}:
        return UNKNOWN_STOCK_STATUS

    human_text = text.replace("_", " ")
    if text in STATUS_ALIASES:
        return STATUS_ALIASES[text]
    if human_text in STATUS_ALIASES:
        return STATUS_ALIASES[human_text]

    if text in USABLE_STOCK_STATUSES | NON_USABLE_STOCK_STATUSES | {UNKNOWN_STOCK_STATUS}:
        return text

    return UNKNOWN_STOCK_STATUS


def is_attention_stock_status(stock_status: Any) -> bool:
    return normalize_stock_status(stock_status) in ATTENTION_STOCK_STATUSES


def is_usable_stock_status(stock_status: Any) -> bool:
    return normalize_stock_status(stock_status) in USABLE_STOCK_STATUSES


def is_low_stock_status(stock_status: Any) -> bool:
    return normalize_stock_status(stock_status) in LOW_STOCK_STATUSES


def is_out_of_stock_status(stock_status: Any) -> bool:
    return normalize_stock_status(stock_status) == "out"


def is_expired_stock_status(stock_status: Any) -> bool:
    return normalize_stock_status(stock_status) == "expired"


def safe_parse_date(value: Any) -> date | None:
    """Parse common ISO-like dates safely.

    Returns None for blanks, invalid dates, and unsupported formats.
    """
    text = normalize_text(value)
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def days_until(target_date: date | None, today: date | None = None) -> int | None:
    if target_date is None:
        return None
    reference_date = today or date.today()
    return (target_date - reference_date).days


def classify_expiry(
    expiry_date: Any,
    today: date | None = None,
    use_soon_days: int = 7,
) -> str:
    """Classify expiry date into a planning-friendly category."""
    raw_text = normalize_text(expiry_date)
    if not raw_text:
        return EXPIRY_NO_DATE

    parsed_date = safe_parse_date(raw_text)
    if parsed_date is None:
        return EXPIRY_INVALID

    days = days_until(parsed_date, today=today)
    if days is None:
        return EXPIRY_NO_DATE
    if days < 0:
        return EXPIRY_EXPIRED
    if days <= use_soon_days:
        return EXPIRY_USE_SOON
    return EXPIRY_FUTURE


def severity_rank(severity: str) -> int:
    return SEVERITY_ORDER.get(normalize_text(severity).lower(), 0)


def build_safety_metadata(requires_confirmation: bool = True) -> dict[str, bool]:
    """Return mandatory safety metadata for read-only planning tools."""
    return {
        "read_only": True,
        "inventory_mutation_performed": False,
        "intake_mutation_performed": False,
        "consumption_mutation_performed": False,
        "waste_mutation_performed": False,
        "shopping_list_mutation_performed": False,
        "requires_user_confirmation_before_write": requires_confirmation,
    }


def build_warning(
    warning_type: str,
    message: str,
    agent_guidance: str,
    severity: str = "medium",
) -> dict[str, str]:
    """Create a standard warning object for agent-facing planning output."""
    return {
        "warning_type": warning_type,
        "severity": severity,
        "message": message,
        "agent_guidance": agent_guidance,
    }


def build_next_action(
    action_type: str,
    label: str,
    tool_name: str,
    reason: str,
    requires_confirmation: bool = True,
) -> dict[str, Any]:
    """Create a standard next-action object for agent tool-routing hints."""
    return {
        "action_type": action_type,
        "label": label,
        "tool_name": tool_name,
        "requires_confirmation": requires_confirmation,
        "reason": reason,
    }
