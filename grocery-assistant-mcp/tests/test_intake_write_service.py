from __future__ import annotations

import pandas as pd
import pytest

from grocery_assistant_mcp.core import grocery_service as service


def test_add_intake_entry_creates_history_row(tmp_path, monkeypatch):
    history_path = tmp_path / "user_intake_history.csv"
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", history_path)

    result = service.add_intake_entry(
        date="2026-05-16",
        time="18:30",
        meal_type="dinner",
        meal_name="Spaghetti bolognese",
        amount_eaten="1 large bowl",
        total_calories_estimate=780,
        nutrition_confidence="medium",
    )

    assert result["success"] is True
    assert result["item"]["intake_id"] == "intake_001"
    assert result["item"]["meal_name"] == "Spaghetti bolognese"
    assert result["backup_created"] is None

    df = pd.read_csv(history_path)
    assert len(df) == 1
    assert df.loc[0, "intake_id"] == "intake_001"
    assert df.loc[0, "meal_type"] == "dinner"
    assert df.loc[0, "total_calories_estimate"] == 780.0


def test_add_intake_entry_rejects_invalid_meal_type(tmp_path, monkeypatch):
    history_path = tmp_path / "user_intake_history.csv"
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", history_path)

    with pytest.raises(ValueError, match="meal_type must be one of"):
        service.add_intake_entry(
            date="2026-05-16",
            meal_type="midnight feast",
            meal_name="Toast",
        )


def test_add_intake_item_requires_existing_parent_intake(tmp_path, monkeypatch):
    history_path = tmp_path / "user_intake_history.csv"
    items_path = tmp_path / "user_intake_items.csv"
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", items_path)

    with pytest.raises(ValueError, match="No intake entry found"):
        service.add_intake_item(
            intake_id="intake_999",
            food_item="Beef mince",
        )


def test_add_intake_item_creates_component_row(tmp_path, monkeypatch):
    history_path = tmp_path / "user_intake_history.csv"
    items_path = tmp_path / "user_intake_items.csv"
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", items_path)

    entry_result = service.add_intake_entry(
        date="2026-05-16",
        time="18:30",
        meal_type="dinner",
        meal_name="Spaghetti bolognese",
    )

    intake_id = entry_result["item"]["intake_id"]

    item_result = service.add_intake_item(
        intake_id=intake_id,
        food_item="Beef mince",
        brand="Coles",
        category="protein",
        source="inventory",
        stock_id="inv_002",
        amount_eaten="1 serve",
        servings_used=1,
        protein_g_estimate=28,
        nutrition_confidence="medium",
    )

    assert item_result["success"] is True
    assert item_result["item"]["intake_item_id"] == "intake_item_001"
    assert item_result["item"]["intake_id"] == intake_id
    assert item_result["item"]["food_item"] == "Beef mince"

    df = pd.read_csv(items_path)
    assert len(df) == 1
    assert df.loc[0, "intake_item_id"] == "intake_item_001"
    assert df.loc[0, "stock_id"] == "inv_002"
    assert df.loc[0, "servings_used"] == 1.0
