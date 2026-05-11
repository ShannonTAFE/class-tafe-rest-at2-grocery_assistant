import json

from grocery_assistant_mcp.core.grocery_service import (
    df_to_records,
    find_inventory_item,
    list_inventory_items,
    read_intake_history,
    read_intake_items,
    read_inventory,
    summarise_intake_day,
    to_json,
)


def test_inventory_records_can_be_converted_to_json():
    df = read_inventory()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert isinstance(payload, str)
    assert isinstance(parsed, list)


def test_inventory_json_payload_contains_records():
    df = read_inventory()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert len(parsed) > 0
    assert isinstance(parsed[0], dict)


def test_intake_history_records_can_be_converted_to_json():
    df = read_intake_history()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert isinstance(payload, str)
    assert isinstance(parsed, list)


def test_intake_history_json_payload_contains_records():
    df = read_intake_history()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert len(parsed) > 0
    assert isinstance(parsed[0], dict)


def test_intake_items_records_can_be_converted_to_json():
    df = read_intake_items()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert isinstance(payload, str)
    assert isinstance(parsed, list)


def test_intake_items_json_payload_contains_records():
    df = read_intake_items()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert len(parsed) > 0
    assert isinstance(parsed[0], dict)


def test_list_inventory_items_payload_is_valid_json():
    items = list_inventory_items()
    payload = to_json(items)

    parsed = json.loads(payload)

    assert isinstance(parsed, list)


def test_find_inventory_item_payload_is_valid_json():
    results = find_inventory_item("rice")
    payload = to_json(results)

    parsed = json.loads(payload)

    assert isinstance(parsed, list)


def test_summarise_intake_day_payload_is_valid_json():
    summary = summarise_intake_day("2026-01-01")
    payload = to_json(summary)

    parsed = json.loads(payload)

    assert isinstance(parsed, dict)
    assert parsed["date"] == "2026-01-01"
    assert "meal_count" in parsed
    assert "item_count" in parsed
    assert "nutrition_totals" in parsed


def test_summarise_intake_day_payload_has_client_friendly_sections():
    summary = summarise_intake_day("2026-01-01")
    payload = to_json(summary)

    parsed = json.loads(payload)

    assert isinstance(parsed["meals"], list)
    assert isinstance(parsed["items"], list)
    assert isinstance(parsed["nutrition_totals"], dict)