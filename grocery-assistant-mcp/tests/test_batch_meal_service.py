from __future__ import annotations

import pandas as pd
import pytest

from grocery_assistant_mcp.core import batch_meal_service as service
from grocery_assistant_mcp.core.schemas import (
    INVENTORY_COLUMNS,
    INTAKE_HISTORY_COLUMNS,
    INTAKE_ITEMS_COLUMNS,
)


@pytest.fixture
def batch_meal_csvs(tmp_path, monkeypatch):
    inventory_path = tmp_path / "user_inventory.csv"
    intake_history_path = tmp_path / "user_intake_history.csv"
    intake_items_path = tmp_path / "user_intake_items.csv"

    pd.DataFrame(
        [
            {
                "stock_id": "inv_001",
                "food_item": "Spaghetti",
                "brand": "San Remo",
                "category": "pantry",
                "location": "cupboard",
                "quantity": 1,
                "unit": "packet",
                "servings_remaining": 5,
                "initial_quantity": 1,
                "initial_servings": 5,
                "stock_status": "in_stock",
                "expiry_date": "2026-12-01",
                "date_added": "2026-05-18",
                "notes": "",
            }
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

    monkeypatch.setattr(service, "INVENTORY_PATH", inventory_path)
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", intake_history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", intake_items_path)

    return {
        "inventory_path": inventory_path,
        "intake_history_path": intake_history_path,
        "intake_items_path": intake_items_path,
    }


def test_add_meal_with_items_creates_parent_and_children(batch_meal_csvs):
    result = service.add_meal_with_items(
        meal_data={
            "date": "2026-05-18",
            "time": "18:30",
            "meal_type": "dinner",
            "meal_name": "Spaghetti bolognese",
            "source": "home",
            "amount_eaten": "1 bowl",
        },
        items=[
            {
                "food_item": "Spaghetti",
                "stock_id": "inv_001",
                "amount_eaten": "1 serve",
                "quantity_used": 100,
                "unit": "g",
            },
            {
                "food_item": "Beef mince",
                "amount_eaten": "1 serve",
                "quantity_used": 125,
                "unit": "g",
            },
        ],
    )

    assert result["success"] is True
    assert result["inventory_deducted"] is False
    assert result["consumption_records_created"] == 0
    assert result["food_waste_records_created"] == 0

    history_df = pd.read_csv(batch_meal_csvs["intake_history_path"])
    items_df = pd.read_csv(batch_meal_csvs["intake_items_path"])

    assert len(history_df) == 1
    assert len(items_df) == 2

    intake_id = history_df.loc[0, "intake_id"]

    assert intake_id == "intake_001"
    assert set(items_df["intake_id"]) == {intake_id}
    assert list(items_df["intake_item_id"]) == [
        "intake_item_001",
        "intake_item_002",
    ]


def test_add_meal_with_items_requires_at_least_one_child_item(batch_meal_csvs):
    with pytest.raises(ValueError, match="items must include at least one"):
        service.add_meal_with_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            items=[],
        )


def test_add_meal_with_items_rejects_invalid_child_without_writing(batch_meal_csvs):
    with pytest.raises(ValueError, match="food_item is required"):
        service.add_meal_with_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            items=[
                {
                    "food_item": "Spaghetti",
                },
                {
                    "food_item": "",
                },
            ],
        )

    history_df = pd.read_csv(batch_meal_csvs["intake_history_path"])
    items_df = pd.read_csv(batch_meal_csvs["intake_items_path"])

    assert history_df.empty
    assert items_df.empty


def test_add_meal_with_items_rejects_unknown_meal_field(batch_meal_csvs):
    with pytest.raises(ValueError, match="meal_data contains unsupported field"):
        service.add_meal_with_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
                "unexpected_field": "bad",
            },
            items=[
                {
                    "food_item": "Spaghetti",
                },
            ],
        )


def test_add_meal_with_items_rejects_unknown_item_field(batch_meal_csvs):
    with pytest.raises(ValueError, match=r"items\[0\] contains unsupported field"):
        service.add_meal_with_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            items=[
                {
                    "food_item": "Spaghetti",
                    "unexpected_field": "bad",
                },
            ],
        )


def test_add_meal_with_items_validates_stock_id_if_supplied(batch_meal_csvs):
    with pytest.raises(ValueError, match="No inventory item found with stock_id"):
        service.add_meal_with_items(
            meal_data={
                "date": "2026-05-18",
                "meal_name": "Spaghetti bolognese",
            },
            items=[
                {
                    "food_item": "Spaghetti",
                    "stock_id": "inv_999",
                },
            ],
        )

    history_df = pd.read_csv(batch_meal_csvs["intake_history_path"])
    items_df = pd.read_csv(batch_meal_csvs["intake_items_path"])

    assert history_df.empty
    assert items_df.empty


def test_add_meal_with_items_does_not_update_inventory(batch_meal_csvs):
    before_inventory_df = pd.read_csv(batch_meal_csvs["inventory_path"])

    service.add_meal_with_items(
        meal_data={
            "date": "2026-05-18",
            "meal_name": "Spaghetti bolognese",
        },
        items=[
            {
                "food_item": "Spaghetti",
                "stock_id": "inv_001",
                "quantity_used": 100,
                "unit": "g",
            },
        ],
    )

    after_inventory_df = pd.read_csv(batch_meal_csvs["inventory_path"])

    pd.testing.assert_frame_equal(before_inventory_df, after_inventory_df)