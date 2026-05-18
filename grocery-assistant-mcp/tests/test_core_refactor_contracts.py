from __future__ import annotations

import importlib


def test_grocery_service_facade_exports_core_public_functions():
    service = importlib.import_module("grocery_assistant_mcp.core.grocery_service")

    expected_functions = [
        # read/resource helpers
        "read_inventory",
        "read_food_waste",
        "read_intake_history",
        "read_intake_items",
        "read_inventory_consumption",
        "df_to_records",
        "to_json",

        # inventory
        "list_inventory_items",
        "find_inventory_item",
        "search_inventory",
        "add_inventory_item",
        "update_inventory_item",
        "remove_inventory_item",

        # intake query/read
        "list_intake_history",
        "list_intake_items",
        "get_recent_intake",
        "get_daily_intake_summary",
        "search_intake",

        # intake write/edit/delete
        "add_intake_entry",
        "update_intake_entry",
        "add_intake_item",
        "update_intake_item",
        "remove_intake_item",
        "remove_intake_entry",

        # inventory consumption
        "list_inventory_consumption",
        "consume_inventory_item",
        "add_intake_item_from_inventory",
    ]

    for function_name in expected_functions:
        assert hasattr(service, function_name), f"Missing export: {function_name}"
        assert callable(getattr(service, function_name))


def test_extracted_core_modules_import_cleanly():
    module_names = [
        "grocery_assistant_mcp.core.schemas",
        "grocery_assistant_mcp.core.constants",
        "grocery_assistant_mcp.core.service_utils",
        "grocery_assistant_mcp.core.csv_store",
        "grocery_assistant_mcp.core.inventory_rules",
        "grocery_assistant_mcp.core.transaction_helpers",
        "grocery_assistant_mcp.core.relationship_helpers",
        "grocery_assistant_mcp.core.consumption_helpers",
        "grocery_assistant_mcp.core.waste_helpers",
        "grocery_assistant_mcp.core.intake_helpers",
    ]

    for module_name in module_names:
        importlib.import_module(module_name)


def test_grocery_csv_paths_fixture_patches_grocery_service_and_csv_store(
    grocery_csv_paths,
):
    from grocery_assistant_mcp.core import csv_store
    from grocery_assistant_mcp.core import grocery_service

    assert grocery_service.INVENTORY_PATH == grocery_csv_paths["INVENTORY_PATH"]
    assert (
        grocery_service.INTAKE_HISTORY_PATH
        == grocery_csv_paths["INTAKE_HISTORY_PATH"]
    )
    assert grocery_service.INTAKE_ITEMS_PATH == grocery_csv_paths["INTAKE_ITEMS_PATH"]
    assert (
        grocery_service.INVENTORY_CONSUMPTION_PATH
        == grocery_csv_paths["INVENTORY_CONSUMPTION_PATH"]
    )
    assert grocery_service.FOOD_WASTE_PATH == grocery_csv_paths["FOOD_WASTE_PATH"]

    assert csv_store.INVENTORY_PATH == grocery_csv_paths["INVENTORY_PATH"]
    assert csv_store.INTAKE_HISTORY_PATH == grocery_csv_paths["INTAKE_HISTORY_PATH"]
    assert csv_store.INTAKE_ITEMS_PATH == grocery_csv_paths["INTAKE_ITEMS_PATH"]
    assert (
        csv_store.INVENTORY_CONSUMPTION_PATH
        == grocery_csv_paths["INVENTORY_CONSUMPTION_PATH"]
    )
    assert csv_store.FOOD_WASTE_PATH == grocery_csv_paths["FOOD_WASTE_PATH"]


def test_future_service_modules_can_be_absent_without_breaking_path_fixture(
    grocery_csv_paths,
):
    """
    The shared path fixture is intentionally forward-compatible.

    Some future service modules such as inventory_service.py or
    batch_meal_service.py may not exist yet. The fixture should still work
    during the gradual Version 1.4 refactor.
    """
    assert grocery_csv_paths["INVENTORY_PATH"].name == "user_inventory.csv"
    assert grocery_csv_paths["INTAKE_HISTORY_PATH"].name == "user_intake_history.csv"
    assert grocery_csv_paths["INTAKE_ITEMS_PATH"].name == "user_intake_items.csv"
    assert (
        grocery_csv_paths["INVENTORY_CONSUMPTION_PATH"].name
        == "user_inventory_consumption.csv"
    )
    assert grocery_csv_paths["FOOD_WASTE_PATH"].name == "user_food_waste.csv"