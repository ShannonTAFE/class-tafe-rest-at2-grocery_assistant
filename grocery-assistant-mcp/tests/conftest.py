from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


CORE_MODULES_WITH_PATHS = [
    # Current public service module.
    "grocery_assistant_mcp.core.grocery_service",

    # New/refactored support module.
    "grocery_assistant_mcp.core.csv_store",

    # Future Version 1.4+ service modules.
    # These may not exist yet, so the fixture imports them safely.
    "grocery_assistant_mcp.core.inventory_service",
    "grocery_assistant_mcp.core.intake_service",
    "grocery_assistant_mcp.core.intake_query_service",
    "grocery_assistant_mcp.core.consumption_service",
    "grocery_assistant_mcp.core.waste_service",
    "grocery_assistant_mcp.core.batch_meal_service",
]


PATH_ATTRS = {
    "INVENTORY_PATH": "user_inventory.csv",
    "INTAKE_HISTORY_PATH": "user_intake_history.csv",
    "INTAKE_ITEMS_PATH": "user_intake_items.csv",
    "INVENTORY_CONSUMPTION_PATH": "user_inventory_consumption.csv",
    "FOOD_WASTE_PATH": "user_food_waste.csv",
}


SCHEMA_ATTRS = {
    "INVENTORY_PATH": "INVENTORY_COLUMNS",
    "INTAKE_HISTORY_PATH": "INTAKE_HISTORY_COLUMNS",
    "INTAKE_ITEMS_PATH": "INTAKE_ITEMS_COLUMNS",
    "INVENTORY_CONSUMPTION_PATH": "INVENTORY_CONSUMPTION_COLUMNS",
    "FOOD_WASTE_PATH": "FOOD_WASTE_COLUMNS",
}


def _import_optional_module(module_name: str):
    """
    Import a module if it exists.

    This keeps test fixtures compatible while Version 1.4 modules are being
    introduced gradually.
    """
    try:
        return import_module(module_name)
    except ModuleNotFoundError:
        return None


def patch_grocery_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    """
    Patch grocery CSV path constants across current and future core modules.

    This prevents tests from accidentally reading/writing real project CSVs
    after service functions are moved out of grocery_service.py.
    """
    paths = {
        attr_name: tmp_path / filename
        for attr_name, filename in PATH_ATTRS.items()
    }

    for module_name in CORE_MODULES_WITH_PATHS:
        module = _import_optional_module(module_name)

        if module is None:
            continue

        for attr_name, path in paths.items():
            if hasattr(module, attr_name):
                monkeypatch.setattr(module, attr_name, path)

    return paths


def write_schema_csv(
    path: Path,
    columns: list[str],
    rows: list[dict] | None = None,
) -> None:
    """
    Write a schema-aligned CSV for tests.
    """
    rows = rows or []
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)


@pytest.fixture()
def grocery_csv_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Path]:
    """
    Patch grocery CSV paths across core modules and return the temp paths.

    This fixture does not automatically create CSV files. Service functions
    using read_csv_for_write can create missing files safely.
    """
    return patch_grocery_paths(monkeypatch, tmp_path)


@pytest.fixture()
def empty_grocery_csvs(grocery_csv_paths: dict[str, Path]) -> dict[str, Path]:
    """
    Patch grocery CSV paths and create empty schema-aligned CSV files.
    """
    from grocery_assistant_mcp.core import schemas

    for path_attr, schema_attr in SCHEMA_ATTRS.items():
        path = grocery_csv_paths[path_attr]
        columns = getattr(schemas, schema_attr)
        write_schema_csv(path, columns)

    return grocery_csv_paths


@pytest.fixture()
def temp_grocery_csv_paths(grocery_csv_paths: dict[str, Path]) -> Path:
    """
    Backwards-compatible fixture for older tests that expect a tmp_path-like
    folder after grocery paths have been patched.
    """
    first_path = next(iter(grocery_csv_paths.values()))
    return first_path.parent