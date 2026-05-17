import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "grocery_assistant_mcp"

DATA_DIR = PACKAGE_ROOT / "mcp_resources" / "data"

USER_INVENTORY_CSV = DATA_DIR / "user_inventory.csv"
USER_INTAKE_HISTORY_CSV = DATA_DIR / "user_intake_history.csv"
USER_INTAKE_ITEMS_CSV = DATA_DIR / "user_intake_items.csv"
USER_INVENTORY_CONSUMPTION_CSV = DATA_DIR / "user_inventory_consumption.csv"
DATA_DESCRIPTIONS_TXT = DATA_DIR / "data_descriptions.txt"
USER_FOOD_WASTE_CSV = DATA_DIR / "user_food_waste.csv"


def get_csv_headers(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or []


def get_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def test_inventory_csv_has_headers():
    assert len(get_csv_headers(USER_INVENTORY_CSV)) > 0


def test_intake_history_csv_has_headers():
    assert len(get_csv_headers(USER_INTAKE_HISTORY_CSV)) > 0


def test_intake_items_csv_has_headers():
    assert len(get_csv_headers(USER_INTAKE_ITEMS_CSV)) > 0


def test_inventory_consumption_csv_has_headers():
    assert len(get_csv_headers(USER_INVENTORY_CONSUMPTION_CSV)) > 0


def test_inventory_csv_has_required_columns():
    headers = set(get_csv_headers(USER_INVENTORY_CSV))

    required_columns = {
        "stock_id",
        "food_item",
        "category",
        "quantity",
        "unit",
        "servings_remaining",
        "stock_status",
    }

    missing_columns = required_columns - headers
    assert not missing_columns, f"Missing columns: {missing_columns}"


def test_inventory_csv_uses_v1_3_stock_status_values():
    rows = get_csv_rows(USER_INVENTORY_CSV)
    allowed_statuses = {"in_stock", "low", "very_low", "out", "expired", ""}

    invalid_rows = [
        row
        for row in rows
        if row.get("stock_status", "").strip().lower() not in allowed_statuses
    ]

    assert not invalid_rows, f"Invalid stock_status rows: {invalid_rows}"


def test_intake_history_csv_has_required_columns():
    headers = set(get_csv_headers(USER_INTAKE_HISTORY_CSV))

    required_columns = {
        "intake_id",
        "date",
        "time",
        "meal_type",
        "meal_name",
    }

    missing_columns = required_columns - headers
    assert not missing_columns, f"Missing columns: {missing_columns}"


def test_intake_items_csv_has_required_columns():
    headers = set(get_csv_headers(USER_INTAKE_ITEMS_CSV))

    required_columns = {
        "intake_item_id",
        "intake_id",
        "food_item",
        "amount_eaten",
        "quantity_used",
        "unit",
        "servings_used",
    }

    missing_columns = required_columns - headers
    assert not missing_columns, f"Missing columns: {missing_columns}"


def test_inventory_consumption_csv_has_required_columns():
    headers = set(get_csv_headers(USER_INVENTORY_CONSUMPTION_CSV))

    required_columns = {
        "consumption_id",
        "stock_id",
        "quantity_used",
        "unit",
        "servings_used",
        "quantity_before",
        "servings_before",
        "quantity_after",
        "servings_after",
        "stock_status_before",
        "stock_status_after",
        "consumed_at",
        "consumption_type",
        "tracking_confidence",
    }

    missing_columns = required_columns - headers
    assert not missing_columns, f"Missing columns: {missing_columns}"


def test_data_descriptions_file_is_not_empty():
    text = DATA_DESCRIPTIONS_TXT.read_text(encoding="utf-8")
    assert len(text.strip()) > 0


def test_food_waste_csv_has_required_columns():
    headers = set(get_csv_headers(USER_FOOD_WASTE_CSV))

    required_columns = {
        "waste_id",
        "stock_id",
        "food_item",
        "quantity_wasted",
        "servings_wasted",
        "wasted_at",
        "waste_type",
        "waste_reason",
        "tracking_confidence",
    }

    missing_columns = required_columns - headers
    assert not missing_columns, f"Missing columns: {missing_columns}"
