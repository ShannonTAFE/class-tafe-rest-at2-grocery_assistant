from datetime import date

from grocery_assistant_mcp.core.planning_helpers import (
    build_safety_metadata,
    classify_expiry,
    is_attention_stock_status,
    is_low_stock_status,
    is_usable_stock_status,
    normalize_stock_status,
    safe_parse_date,
)


def test_normalize_stock_status_handles_blank_as_unknown():
    assert normalize_stock_status("") == "unknown"
    assert normalize_stock_status(None) == "unknown"


def test_normalize_stock_status_maps_ok_to_in_stock():
    assert normalize_stock_status("ok") == "in_stock"
    assert normalize_stock_status("in stock") == "in_stock"


def test_low_stock_status_detects_low_and_very_low():
    assert is_low_stock_status("low") is True
    assert is_low_stock_status("very_low") is True
    assert is_low_stock_status("in_stock") is False


def test_attention_status_detects_relevant_statuses():
    assert is_attention_stock_status("low") is True
    assert is_attention_stock_status("out") is True
    assert is_attention_stock_status("expired") is True
    assert is_attention_stock_status("in_stock") is False


def test_usable_status_detects_available_statuses():
    assert is_usable_stock_status("in_stock") is True
    assert is_usable_stock_status("low") is True
    assert is_usable_stock_status("very_low") is True
    assert is_usable_stock_status("out") is False


def test_safe_parse_date_handles_iso_and_blank():
    assert safe_parse_date("2026-05-19") == date(2026, 5, 19)
    assert safe_parse_date("") is None
    assert safe_parse_date("not-a-date") is None


def test_classify_expiry_returns_expired():
    assert classify_expiry("2026-05-18", today=date(2026, 5, 19)) == "expired"


def test_classify_expiry_returns_use_soon():
    assert classify_expiry("2026-05-21", today=date(2026, 5, 19), use_soon_days=7) == "use_soon"


def test_classify_expiry_returns_future():
    assert classify_expiry("2026-06-19", today=date(2026, 5, 19), use_soon_days=7) == "future"


def test_classify_expiry_returns_no_expiry_date():
    assert classify_expiry("", today=date(2026, 5, 19)) == "no_expiry_date"


def test_build_safety_metadata_is_read_only():
    safety = build_safety_metadata()

    assert safety["read_only"] is True
    assert safety["inventory_mutation_performed"] is False
    assert safety["intake_mutation_performed"] is False
    assert safety["consumption_mutation_performed"] is False
    assert safety["waste_mutation_performed"] is False
    assert safety["shopping_list_mutation_performed"] is False
    assert safety["requires_user_confirmation_before_write"] is True
