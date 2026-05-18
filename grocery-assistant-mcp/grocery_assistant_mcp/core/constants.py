from __future__ import annotations


VALID_STOCK_STATUSES = {
    "in_stock",
    "low",
    "very_low",
    "out",
    "expired",
}


VALID_REMOVAL_TYPES = {
    "used_up",
    "expired",
    "spoiled",
    "discarded",
    "unused",
    "overbought",
    "did_not_like",
    "duplicate_entry",
    "incorrect_entry",
    "test_entry",
    "no_longer_tracked",
    "unknown",
}


WASTE_REMOVAL_TYPES = {
    "expired",
    "spoiled",
    "discarded",
    "unused",
    "overbought",
    "did_not_like",
}


VALID_TRACKING_CONFIDENCE = {
    "low",
    "medium",
    "high",
}


VALID_MEAL_TYPES = {
    "breakfast",
    "brunch",
    "lunch",
    "dinner",
    "snack",
    "drink",
    "dessert",
    "supper",
    "meal",
    "other",
    "unknown",
}


VALID_CONSUMPTION_TYPES = {
    "consumed",
    "used_in_cooking",
    "finished",
    "adjustment",
    "other",
}


VALID_CONFIDENCE_LEVELS = {
    "low",
    "medium",
    "high",
    "unknown",
}


VALID_YES_NO_UNKNOWN = {
    "yes",
    "no",
    "unknown",
}


VALID_FINISHED_STATUSES = {
    "yes",
    "no",
    "partial",
    "unknown",
}