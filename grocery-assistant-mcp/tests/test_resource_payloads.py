import json

from grocery_assistant_mcp.core.grocery_service import (
    df_to_records,
    find_inventory_item,
    list_inventory_items,
    read_intake_history,
    read_intake_items,
    read_inventory,
    get_daily_intake_summary,
    to_json,
    list_food_waste_items,
    read_food_waste,
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


def test_get_daily_intake_summary_payload_is_valid_json():
    summary = get_daily_intake_summary("2026-01-01")
    payload = to_json(summary)

    parsed = json.loads(payload)

    assert isinstance(parsed, dict)
    assert parsed["date"] == "2026-01-01"
    assert "meal_count" in parsed
    assert "item_count" in parsed
    assert "nutrition_totals" in parsed


def test_get_daily_intake_summary_payload_has_client_friendly_sections():
    summary = get_daily_intake_summary("2026-01-01")
    payload = to_json(summary)

    parsed = json.loads(payload)

    assert isinstance(parsed["meals"], list)
    assert isinstance(parsed["items"], list)
    assert isinstance(parsed["nutrition_totals"], dict)
    
def test_food_waste_records_can_be_converted_to_json():
    df = read_food_waste()
    records = df_to_records(df)
    payload = to_json(records)

    parsed = json.loads(payload)

    assert isinstance(payload, str)
    assert isinstance(parsed, list)


def test_list_food_waste_items_payload_is_valid_json():
    items = list_food_waste_items()
    payload = to_json(items)

    parsed = json.loads(payload)

    assert isinstance(parsed, list)


def test_list_expired_food_waste_items_payload_is_valid_json():
    items = list_food_waste_items(waste_type="expired")
    payload = to_json(items)

    parsed = json.loads(payload)

    assert isinstance(parsed, list)

    for item in parsed:
        assert item.get("waste_type", "").lower() == "expired"