from __future__ import annotations

import math

import pytest

from grocery_assistant_mcp.core.write_helpers import (
    clean_text,
    validate_int_range,
    validate_non_negative_number,
    validate_required_date,
)


def test_clean_text_required_rejects_blank():
    with pytest.raises(ValueError, match="food_item is required"):
        clean_text("   ", "food_item", required=True)


def test_validate_non_negative_number_rejects_nan_and_infinity():
    for value in [math.nan, math.inf, -math.inf]:
        with pytest.raises(ValueError, match="finite"):
            validate_non_negative_number(value, "quantity")


def test_validate_non_negative_number_rejects_boolean():
    with pytest.raises(ValueError, match="not a boolean"):
        validate_non_negative_number(True, "quantity")


def test_validate_required_date_rejects_blank_and_bad_format():
    with pytest.raises(ValueError, match="date is required"):
        validate_required_date("", "date")

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        validate_required_date("16/05/2026", "date")


def test_validate_int_range_rejects_out_of_range():
    with pytest.raises(ValueError, match="between 0 and 365"):
        validate_int_range(999, "days_back", 0, 365)
