from __future__ import annotations

import pandas as pd
import pytest

from grocery_assistant_mcp.core import batch_inventory_meal_service as service
from grocery_assistant_mcp.core.schemas import (
    INVENTORY_COLUMNS,
    INVENTORY_CONSUMPTION_COLUMNS,
    INTAKE_HISTORY_COLUMNS,
    INTAKE_ITEMS_COLUMNS,
)


@pytest.fixture
def batch_inventory_meal_csvs(tmp_path, monkeypatch):
    inventory_path = tmp_path / "user_inventory.csv"
    intake_history_path = tmp_path / "user_intake_history.csv"
    intake_items_path = tmp_path / "user_intake_items.csv"
    consumption_path = tmp_path / "user_inventory_consumption.csv"

    pd.DataFrame(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Spaghetti",
                "brand": "San Remo",
                "category": "pantry",
                "location": "cupboard",
                "quantity": 500,
                "unit": "g",
                "servings_remaining": 5,
                "initial_quantity": 500,
                "initial_servings": 5,
                "stock_status": "in_stock",
                "expiry_date": "2026-12-01",
                "date_added": "2026-05-18",
                "notes": "",
            },
            {
                "stock_id": "inv_002",
                "food_item": "Beef mince",
                "brand": "",
                "category": "protein",
                "location": "freezer",
                "quantity": 500,
                "unit": "g",
                "servings_remaining": 4,
                "initial_quantity": 500,
                "initial_servings": 4,
                "stock_status": "in_stock",
                "expiry_date": "2026-08-01",
                "date_added": "2026-05-18",
                "notes": "",
            },
        ],
        columns=INVENTORY_COLUMNS,
    ).to_csv(inventory_path, index=False)

    pd.DataFrame(columns=INTAKE_HISTORY_COLUMNS).to_csv(
        intake_history_path,
        index=False,
    )

    pd.DataFrame(columns=INTAKE_ITEMS_COLUMNS).to_csv(
        intake_items_path,
        index=False,
    )

    pd.DataFrame(columns=INVENTORY_CONSUMPTION_COLUMNS).to_csv(
        consumption_path,
        index=False,
    )

    monkeypatch.setattr(service, "INVENTORY_PATH", inventory_path)
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", intake_history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", intake_items_path)
    monkeypatch.setattr(service, "INVENTORY_CONSUMPTION_PATH", consumption_path)

    return {
        "inventory_path": inventory_path,
        "intake_history_path": intake_history_path,
        "intake_items_path": intake_items_path,
        "consumption_path": consumption_path,
    }


def read_all(paths: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    history_df = pd.read_csv(paths["intake_history_path"])
    items_df = pd.read_csv(paths["intake_items_path"])
    inventory_df = pd.read_csv(paths["inventory_path"])
    consumption_df = pd.read_csv(paths["consumption_path"])

    return history_df, items_df, inventory_df, consumption_df


def test_add_meal_with_inventory_items_creates_linked_records(
    batch_inventory_meal_csvs,
):
    result = service.add_meal_with_inventory_items(
        meal_data={
            "date": "2026-05-18",
            "time": "18:30",
            "meal_type": "dinner",
            "meal_name": "Spaghetti bolognese",
            "source": "home",
            "amount_eaten": "1 bowl",
        },
        inventory_items=[
            {
                "stock_id": "inv_001",
                "amount_eaten": "1 serve",
                "quantity_used": 100,
                "servings_used": 1,
                "calories_estimate": 360,
                "nutrition_confidence": "medium",
                "consumption_type": "consumed",
                "tracking_confidence": "medium",
            },
            {
                "stock_id": "inv_002",
                "amount_eaten": "1 serve",
                "quantity_used": 125,
                "servings_used": 1,
                "calories_estimate": 300,
                "nutrition_confidence": "medium",
                "consumption_type": "consumed",
                "tracking_confidence": "medium",
            },
        ],
        manual_items=[
            {
                "food_item": "Parmesan",
                "category": "dairy",
                "source": "home",
                "amount_eaten": "small topping",
                "quantity_used": 10,
                "unit": "g",
                "nutrition_confidence": "low",
            }
        ],
    )

    assert result["success"] is True
    assert result["inventory_deducted"] is True
    assert result["item_count"] == 3
    assert result["inventory_item_count"] == 2
    assert result["manual_item_count"] == 1
    assert result["consumption_records_created"] == 2
    assert result["food_waste_records_created"] == 0

    history_df, items_df, inventory_df, consumption_df = read_all(
        batch_inventory_meal_csvs,
    )

    assert len(history_df) == 1
    assert len(items_df) == 3
    assert len(consumption_df) == 2

    assert history_df.loc[0, "intake_id"] == "intake_001"
    assert set(items_df["intake_id"]) == {"intake_001"}

    assert list(items_df["intake_item_id"]) == [
        "intake_item_001",
        "intake_item_002",
        "intake_item_003",
    ]

    assert list(consumption_df["consumption_id"]) == [
        "consumption_001",
        "consumption_002",
    ]

    assert set(consumption_df["intake_id"]) == {"intake_001"}
    assert set(consumption_df["intake_item_id"]) == {
        "intake_item_001",
        "intake_item_002",
    }

    spaghetti_item = items_df[items_df["stock_id"] == "inv_001"].iloc[0]
    mince_item = items_df[items_df["stock_id"] == "inv_002"].iloc[0]
    manual_item = items_df[items_df["food_item"] == "Parmesan"].iloc[0]

    assert spaghetti_item["food_item"] == "Spaghetti"
    assert spaghetti_item["unit"] == "g"
    assert mince_item["food_item"] == "Beef mince"
    assert mince_item["unit"] == "g"
    assert pd.isna(manual_item["stock_id"]) or manual_item["stock_id"] == ""

    spaghetti_row = inventory_df[inventory_df["stock_id"] == "inv_001"].iloc[0]
    mince_row = inventory_df[inventory_df["stock_id"] == "inv_002"].iloc[0]

    assert spaghetti_row["quantity"] == 400
    assert spaghetti_row["servings_remaining"] == 4
    assert mince_row["quantity"] == 375
    assert mince_row["servings_remaining"] == 3


def test_add_meal_with_inventory_items_supports_manual_items_without_consumption(
    batch_inventory_meal_csvs,
):
    result = service.add_meal_with_inventory_items(
        meal_data={
            "date": "2026-05-18",
            "meal_name": "Snack plate",
        },
        inventory_items=[
            {
                "stock_id": "inv_001",
                "quantity_used": 100,
                "servings_used": 1,
            }
        ],
        manual_items=[
            {
                "food_item": "Cheese",
                "category": "dairy",
                "quantity_used": 30,
                "unit": "g",
            },
            {
                "food_item": "Crackers",
                "category": "pantry",
                "quantity_used": 20,
                "unit": "g",
            },
        ],
    )

    assert result["item_count"] == 3
    assert result["inventory_item_count"] == 1
    assert result["manual_item_count"] == 2
    assert result["consumption_records_created"] == 1

    _history_df, items_df, _inventory_df, consumption_df = read_all(
        batch_inventory_meal_csvs,
    )

    assert len(items_df) == 3
    assert len(consumption_df) == 1
    assert set(consumption_df["stock_id"]) == {"inv_001"}


def test_add_meal_with_inventory_items_rejects_duplicate_stock_id_without_writing(
    batch_inventory_meal_csvs,
):
    before = read_all(batch_inventory_meal_csvs)

    with pytest.raises(ValueError, match="Duplicate stock_id"):
        service.add_meal_with_inventory_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            inventory_items=[
                {
                    "stock_id": "inv_001",
                    "quantity_used": 50,
                },
                {
                    "stock_id": "inv_001",
                    "quantity_used": 50,
                },
            ],
        )

    after = read_all(batch_inventory_meal_csvs)

    for before_df, after_df in zip(before, after):
        pd.testing.assert_frame_equal(before_df, after_df)


def test_add_meal_with_inventory_items_rejects_unknown_stock_id_without_writing(
    batch_inventory_meal_csvs,
):
    before = read_all(batch_inventory_meal_csvs)

    with pytest.raises(ValueError, match="No inventory item found with stock_id"):
        service.add_meal_with_inventory_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            inventory_items=[
                {
                    "stock_id": "inv_999",
                    "quantity_used": 100,
                },
            ],
        )

    after = read_all(batch_inventory_meal_csvs)

    for before_df, after_df in zip(before, after):
        pd.testing.assert_frame_equal(before_df, after_df)


def test_add_meal_with_inventory_items_rejects_over_consumption_without_writing(
    batch_inventory_meal_csvs,
):
    before = read_all(batch_inventory_meal_csvs)

    with pytest.raises(ValueError):
        service.add_meal_with_inventory_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            inventory_items=[
                {
                    "stock_id": "inv_001",
                    "quantity_used": 9999,
                },
            ],
        )

    after = read_all(batch_inventory_meal_csvs)

    for before_df, after_df in zip(before, after):
        pd.testing.assert_frame_equal(before_df, after_df)


def test_add_meal_with_inventory_items_rejects_stock_id_in_manual_items(
    batch_inventory_meal_csvs,
):
    before = read_all(batch_inventory_meal_csvs)

    with pytest.raises(ValueError, match="must not include stock_id"):
        service.add_meal_with_inventory_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            inventory_items=[
                {
                    "stock_id": "inv_001",
                    "quantity_used": 100,
                },
            ],
            manual_items=[
                {
                    "food_item": "Parmesan",
                    "stock_id": "inv_999",
                },
            ],
        )

    after = read_all(batch_inventory_meal_csvs)

    for before_df, after_df in zip(before, after):
        pd.testing.assert_frame_equal(before_df, after_df)


def test_add_meal_with_inventory_items_requires_inventory_items(
    batch_inventory_meal_csvs,
):
    with pytest.raises(ValueError, match="inventory_items must include at least one"):
        service.add_meal_with_inventory_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            inventory_items=[],
        )