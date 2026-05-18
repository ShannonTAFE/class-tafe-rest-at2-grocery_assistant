from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from grocery_assistant_mcp.utils.paths import (
    INVENTORY_PATH,
    INTAKE_HISTORY_PATH,
    INTAKE_ITEMS_PATH,
    INVENTORY_CONSUMPTION_PATH,
    FOOD_WASTE_PATH,
)

from grocery_assistant_mcp.core.schemas import (
    INVENTORY_COLUMNS,
    INTAKE_HISTORY_COLUMNS,
    INTAKE_ITEMS_COLUMNS,
    INVENTORY_CONSUMPTION_COLUMNS,
    FOOD_WASTE_COLUMNS,
)

from grocery_assistant_mcp.core.write_helpers import read_csv_for_write


logger = logging.getLogger("grocery_mcp.grocery_data")


def read_csv_file(path: Path) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame.

    If the file does not exist, return an empty DataFrame instead of crashing
    the MCP server.
    """
    if not path.exists():
        logger.warning("CSV file not found: %s", path)
        return pd.DataFrame()

    return pd.read_csv(path)


def read_inventory() -> pd.DataFrame:
    """
    Read user_inventory.csv as the user's tracked grocery stock state.
    """
    return read_csv_file(INVENTORY_PATH)


def read_food_waste() -> pd.DataFrame:
    """
    Read user_food_waste.csv.
    """
    return read_csv_file(FOOD_WASTE_PATH)


def read_intake_history() -> pd.DataFrame:
    """
    Read user_intake_history.csv.
    """
    return read_csv_file(INTAKE_HISTORY_PATH)


def read_intake_items() -> pd.DataFrame:
    """
    Read user_intake_items.csv.
    """
    return read_csv_file(INTAKE_ITEMS_PATH)


def read_inventory_consumption() -> pd.DataFrame:
    """
    Read user_inventory_consumption.csv.
    """
    return read_csv_file(INVENTORY_CONSUMPTION_PATH)


def read_inventory_for_write() -> pd.DataFrame:
    """
    Read user_inventory.csv for write workflows.

    Missing files return an empty DataFrame with the expected schema.
    """
    return read_csv_for_write(INVENTORY_PATH, INVENTORY_COLUMNS)


def read_food_waste_for_write() -> pd.DataFrame:
    """
    Read user_food_waste.csv for write workflows.

    Missing files return an empty DataFrame with the expected schema.
    """
    return read_csv_for_write(FOOD_WASTE_PATH, FOOD_WASTE_COLUMNS)


def read_intake_history_for_write() -> pd.DataFrame:
    """
    Read user_intake_history.csv for write workflows.

    Missing files return an empty DataFrame with the expected schema.
    """
    return read_csv_for_write(INTAKE_HISTORY_PATH, INTAKE_HISTORY_COLUMNS)


def read_intake_items_for_write() -> pd.DataFrame:
    """
    Read user_intake_items.csv for write workflows.

    Missing files return an empty DataFrame with the expected schema.
    """
    return read_csv_for_write(INTAKE_ITEMS_PATH, INTAKE_ITEMS_COLUMNS)


def read_inventory_consumption_for_write() -> pd.DataFrame:
    """
    Read user_inventory_consumption.csv for write workflows.

    Missing files return an empty DataFrame with the expected schema.
    """
    return read_csv_for_write(
        INVENTORY_CONSUMPTION_PATH,
        INVENTORY_CONSUMPTION_COLUMNS,
    )