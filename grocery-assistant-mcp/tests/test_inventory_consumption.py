import pandas as pd
import pytest

from grocery_assistant_mcp.core import grocery_service as service


@pytest.fixture
def consumption_csvs(tmp_path, monkeypatch):
    inventory_path = tmp_path / "user_inventory.csv"
    intake_history_path = tmp_path / "user_intake_history.csv"
    intake_items_path = tmp_path / "user_intake_items.csv"
    food_waste_path = tmp_path / "user_food_waste.csv"

    monkeypatch.setattr(service, "INVENTORY_PATH", inventory_path)
    monkeypatch.setattr(service, "INTAKE_HISTORY_PATH", intake_history_path)
    monkeypatch.setattr(service, "INTAKE_ITEMS_PATH", intake_items_path)
    monkeypatch.setattr(service, "FOOD_WASTE_PATH", food_waste_path)

    inventory_rows = [
        {
            "stock_id": "inv_001",
            "food_item": "Chicken breast",
            "brand": "Coles",
            "category": "protein",
            "location": "freezer",
            "quantity": 500,
            "unit": "g",
            "servings_remaining": 4,
            "initial_quantity": 500,
            "initial_servings": 4,
            "stock_status": "ok",
            "expiry_date": "2026-06-01",
            "date_added": "2026-05-10",
            "notes": "Test chicken",
        },
        {
            "stock_id": "inv_002",
            "food_item": "Rice",
            "brand": "",
            "category": "pantry",
            "location": "cupboard",
            "quantity": 1000,
            "unit": "g",
            "servings_remaining": 10,
            "initial_quantity": 1000,
            "initial_servings": 10,
            "stock_status": "ok",
            "expiry_date": "2027-01-01",
            "date_added": "2026-05-10",
            "notes": "Test rice",
        },
        {
            "stock_id": "inv_003",
            "food_item": "Greek yoghurt",
            "brand": "Chobani",
            "category": "dairy",
            "location": "fridge",
            "quantity": 1,
            "unit": "tub",
            "servings_remaining": 1,
            "initial_quantity": 1,
            "initial_servings": 1,
            "stock_status": "low",
            "expiry_date": "2026-05-20",
            "date_added": "2026-05-10",
            "notes": "Nearly finished",
        },
    ]

    pd.DataFrame(inventory_rows, columns=service.INVENTORY_COLUMNS).to_csv(
        inventory_path,
        index=False,
    )

    intake_history_rows = [
        {
            "intake_id": "intake_001",
            "date": "2026-05-17",
            "time": "08:00",
            "meal_type": "breakfast",
            "meal_name": "Existing breakfast",
            "meal_description": "",
            "source": "home",
            "amount_eaten": "",
            "portion_confidence": "medium",
            "total_calories_estimate": 0,
            "total_protein_g_estimate": 0,
            "total_carbs_g_estimate": 0,
            "total_fat_g_estimate": 0,
            "total_fibre_g_estimate": 0,
            "total_sugar_g_estimate": 0,
            "total_sodium_mg_estimate": 0,
            "nutrition_confidence": "medium",
            "was_finished": "unknown",
            "leftovers_created": "unknown",
            "hunger_before": "",
            "hunger_after": "",
            "notes": "",
        }
    ]

    pd.DataFrame(intake_history_rows, columns=service.INTAKE_HISTORY_COLUMNS).to_csv(
        intake_history_path,
        index=False,
    )

    intake_item_rows = [
        {
            "intake_item_id": "intake_item_001",
            "intake_id": "intake_001",
            "food_item": "Existing item",
            "brand": "",
            "category": "",
            "source": "manual",
            "stock_id": "",
            "amount_eaten": "",
            "servings_used": 0,
            "calories_estimate": 0,
            "protein_g_estimate": 0,
            "carbs_g_estimate": 0,
            "fat_g_estimate": 0,
            "fibre_g_estimate": 0,
            "sugar_g_estimate": 0,
            "sodium_mg_estimate": 0,
            "nutrition_confidence": "medium",
            "notes": "",
        }
    ]

    pd.DataFrame(intake_item_rows, columns=service.INTAKE_ITEMS_COLUMNS).to_csv(
        intake_items_path,
        index=False,
    )

    pd.DataFrame(columns=service.FOOD_WASTE_COLUMNS).to_csv(
        food_waste_path,
        index=False,
    )

    return {
        "inventory_path": inventory_path,
        "intake_history_path": intake_history_path,
        "intake_items_path": intake_items_path,
        "food_waste_path": food_waste_path,
    }


def inventory_row(path, stock_id):
    df = pd.read_csv(path).fillna("")
    row = df[df["stock_id"].astype(str).str.strip() == stock_id].iloc[0]
    return row.to_dict()


def test_consume_inventory_item_reduces_servings(consumption_csvs):
    result = service.consume_inventory_item(
        stock_id="inv_001",
        servings_used=1,
    )

    assert result["success"] is True
    assert result["stock_id"] == "inv_001"
    assert result["servings_used"] == 1.0

    assert float(result["inventory_before"]["servings_remaining"]) == 4.0
    assert float(result["inventory_after"]["servings_remaining"]) == 3.0

    row = inventory_row(consumption_csvs["inventory_path"], "inv_001")
    assert float(row["servings_remaining"]) == 3.0
    assert float(row["quantity"]) == 500.0
    assert row["stock_status"] == "ok"


def test_consume_inventory_item_reduces_quantity(consumption_csvs):
    result = service.consume_inventory_item(
        stock_id="inv_001",
        quantity_used=125,
    )

    assert result["success"] is True
    assert result["quantity_used"] == 125.0

    row = inventory_row(consumption_csvs["inventory_path"], "inv_001")
    assert float(row["quantity"]) == 375.0
    assert float(row["servings_remaining"]) == 4.0
    assert row["stock_status"] == "ok"


def test_consume_inventory_item_reduces_quantity_and_servings(consumption_csvs):
    service.consume_inventory_item(
        stock_id="inv_002",
        quantity_used=200,
        servings_used=2,
    )

    row = inventory_row(consumption_csvs["inventory_path"], "inv_002")
    assert float(row["quantity"]) == 800.0
    assert float(row["servings_remaining"]) == 8.0
    assert row["stock_status"] == "ok"


def test_consume_inventory_item_exact_remaining_marks_out(consumption_csvs):
    result = service.consume_inventory_item(
        stock_id="inv_003",
        quantity_used=1,
        servings_used=1,
    )

    assert float(result["inventory_after"]["quantity"]) == 0.0
    assert float(result["inventory_after"]["servings_remaining"]) == 0.0
    assert result["inventory_after"]["stock_status"] == "out"

    row = inventory_row(consumption_csvs["inventory_path"], "inv_003")
    assert float(row["quantity"]) == 0.0
    assert float(row["servings_remaining"]) == 0.0
    assert row["stock_status"] == "out"


def test_consume_inventory_item_rejects_over_consumed_quantity(consumption_csvs):
    before = consumption_csvs["inventory_path"].read_text()

    with pytest.raises(ValueError, match="quantity_used cannot exceed current quantity"):
        service.consume_inventory_item(
            stock_id="inv_001",
            quantity_used=999,
        )

    after = consumption_csvs["inventory_path"].read_text()
    assert after == before


def test_consume_inventory_item_rejects_over_consumed_servings(consumption_csvs):
    before = consumption_csvs["inventory_path"].read_text()

    with pytest.raises(ValueError, match="servings_used cannot exceed current servings"):
        service.consume_inventory_item(
            stock_id="inv_001",
            servings_used=999,
        )

    after = consumption_csvs["inventory_path"].read_text()
    assert after == before


def test_consume_inventory_item_rejects_zero_consumption(consumption_csvs):
    before = consumption_csvs["inventory_path"].read_text()

    with pytest.raises(ValueError, match="At least one of quantity_used or servings_used must be greater than 0"):
        service.consume_inventory_item(
            stock_id="inv_001",
            quantity_used=0,
            servings_used=0,
        )

    after = consumption_csvs["inventory_path"].read_text()
    assert after == before


def test_consume_inventory_item_rejects_negative_consumption(consumption_csvs):
    before = consumption_csvs["inventory_path"].read_text()

    with pytest.raises(ValueError, match="quantity_used must not be negative"):
        service.consume_inventory_item(
            stock_id="inv_001",
            quantity_used=-1,
        )

    after = consumption_csvs["inventory_path"].read_text()
    assert after == before


def test_consume_inventory_item_rejects_missing_stock_id(consumption_csvs):
    before = consumption_csvs["inventory_path"].read_text()

    with pytest.raises(ValueError, match="No inventory item found with stock_id: inv_999"):
        service.consume_inventory_item(
            stock_id="inv_999",
            servings_used=1,
        )

    after = consumption_csvs["inventory_path"].read_text()
    assert after == before


def test_consume_inventory_item_does_not_touch_intake_files(consumption_csvs):
    before_history = consumption_csvs["intake_history_path"].read_text()
    before_items = consumption_csvs["intake_items_path"].read_text()

    service.consume_inventory_item(
        stock_id="inv_001",
        servings_used=1,
    )

    after_history = consumption_csvs["intake_history_path"].read_text()
    after_items = consumption_csvs["intake_items_path"].read_text()

    assert after_history == before_history
    assert after_items == before_items

def intake_items_df(path):
    return pd.read_csv(path).fillna("")


def test_add_intake_item_from_inventory_creates_item_and_consumes_serving(consumption_csvs):
    result = service.add_intake_item_from_inventory(
        intake_id="intake_001",
        stock_id="inv_001",
        amount_eaten="1 serving",
        servings_used=1,
        calories_estimate=165,
        protein_g_estimate=31,
        carbs_g_estimate=0,
        fat_g_estimate=4,
        nutrition_confidence="high",
        notes="Used from freezer stock",
    )

    assert result["success"] is True
    assert result["intake_item"]["intake_item_id"] == "intake_item_002"
    assert result["intake_item"]["intake_id"] == "intake_001"
    assert result["intake_item"]["food_item"] == "Chicken breast"
    assert result["intake_item"]["brand"] == "Coles"
    assert result["intake_item"]["category"] == "protein"
    assert result["intake_item"]["source"] == "inventory"
    assert result["intake_item"]["stock_id"] == "inv_001"
    assert result["intake_item"]["amount_eaten"] == "1 serving"
    assert float(result["intake_item"]["servings_used"]) == 1.0
    assert float(result["intake_item"]["calories_estimate"]) == 165.0
    assert result["intake_item"]["nutrition_confidence"] == "high"

    assert float(result["inventory_before"]["servings_remaining"]) == 4.0
    assert float(result["inventory_after"]["servings_remaining"]) == 3.0

    inventory = inventory_row(consumption_csvs["inventory_path"], "inv_001")
    assert float(inventory["servings_remaining"]) == 3.0
    assert float(inventory["quantity"]) == 500.0
    assert inventory["stock_status"] == "ok"

    items = intake_items_df(consumption_csvs["intake_items_path"])
    assert len(items) == 2

    created = items[items["intake_item_id"] == "intake_item_002"].iloc[0].to_dict()
    assert created["food_item"] == "Chicken breast"
    assert created["source"] == "inventory"
    assert created["stock_id"] == "inv_001"


def test_add_intake_item_from_inventory_consumes_quantity(consumption_csvs):
    result = service.add_intake_item_from_inventory(
        intake_id="intake_001",
        stock_id="inv_001",
        amount_eaten="125g",
        quantity_used=125,
        calories_estimate=165,
        protein_g_estimate=31,
    )

    assert result["success"] is True
    assert result["quantity_used"] == 125.0
    assert result["servings_used"] == 0.0

    inventory = inventory_row(consumption_csvs["inventory_path"], "inv_001")
    assert float(inventory["quantity"]) == 375.0
    assert float(inventory["servings_remaining"]) == 4.0

    items = intake_items_df(consumption_csvs["intake_items_path"])
    created = items[items["intake_item_id"] == "intake_item_002"].iloc[0].to_dict()
    assert created["amount_eaten"] == "125g"
    assert float(created["servings_used"]) == 0.0


def test_add_intake_item_from_inventory_exact_remaining_marks_inventory_out(consumption_csvs):
    result = service.add_intake_item_from_inventory(
        intake_id="intake_001",
        stock_id="inv_003",
        amount_eaten="last tub",
        quantity_used=1,
        servings_used=1,
    )

    assert result["success"] is True
    assert result["inventory_after"]["stock_status"] == "out"

    inventory = inventory_row(consumption_csvs["inventory_path"], "inv_003")
    assert float(inventory["quantity"]) == 0.0
    assert float(inventory["servings_remaining"]) == 0.0
    assert inventory["stock_status"] == "out"

    items = intake_items_df(consumption_csvs["intake_items_path"])
    created = items[items["intake_item_id"] == "intake_item_002"].iloc[0].to_dict()
    assert created["food_item"] == "Greek yoghurt"
    assert created["category"] == "dairy"
    assert created["source"] == "inventory"


def test_add_intake_item_from_inventory_rejects_invalid_intake_id_without_writes(consumption_csvs):
    before_inventory = consumption_csvs["inventory_path"].read_text()
    before_items = consumption_csvs["intake_items_path"].read_text()

    with pytest.raises(ValueError, match="No intake entry found with intake_id: intake_999"):
        service.add_intake_item_from_inventory(
            intake_id="intake_999",
            stock_id="inv_001",
            servings_used=1,
        )

    assert consumption_csvs["inventory_path"].read_text() == before_inventory
    assert consumption_csvs["intake_items_path"].read_text() == before_items


def test_add_intake_item_from_inventory_rejects_invalid_stock_id_without_writes(consumption_csvs):
    before_inventory = consumption_csvs["inventory_path"].read_text()
    before_items = consumption_csvs["intake_items_path"].read_text()

    with pytest.raises(ValueError, match="No inventory item found with stock_id: inv_999"):
        service.add_intake_item_from_inventory(
            intake_id="intake_001",
            stock_id="inv_999",
            servings_used=1,
        )

    assert consumption_csvs["inventory_path"].read_text() == before_inventory
    assert consumption_csvs["intake_items_path"].read_text() == before_items


def test_add_intake_item_from_inventory_rejects_overconsumption_without_writes(consumption_csvs):
    before_inventory = consumption_csvs["inventory_path"].read_text()
    before_items = consumption_csvs["intake_items_path"].read_text()

    with pytest.raises(ValueError, match="servings_used cannot exceed current servings"):
        service.add_intake_item_from_inventory(
            intake_id="intake_001",
            stock_id="inv_001",
            servings_used=999,
        )

    assert consumption_csvs["inventory_path"].read_text() == before_inventory
    assert consumption_csvs["intake_items_path"].read_text() == before_items


def test_add_intake_item_from_inventory_rejects_invalid_nutrition_confidence_without_writes(consumption_csvs):
    before_inventory = consumption_csvs["inventory_path"].read_text()
    before_items = consumption_csvs["intake_items_path"].read_text()

    with pytest.raises(ValueError, match="nutrition_confidence must be blank or one of"):
        service.add_intake_item_from_inventory(
            intake_id="intake_001",
            stock_id="inv_001",
            servings_used=1,
            nutrition_confidence="certain",
        )

    assert consumption_csvs["inventory_path"].read_text() == before_inventory
    assert consumption_csvs["intake_items_path"].read_text() == before_items