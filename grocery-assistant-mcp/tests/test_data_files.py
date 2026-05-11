import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "grocery_assistant_mcp"

DATA_DIR = PACKAGE_ROOT / "mcp_resources" / "data"

USER_INVENTORY_CSV = DATA_DIR / "user_inventory.csv"
USER_INTAKE_HISTORY_CSV = DATA_DIR / "user_intake_history.csv"
USER_INTAKE_ITEMS_CSV = DATA_DIR / "user_intake_items.csv"
DATA_DESCRIPTIONS_TXT = DATA_DIR / "data_descriptions.txt"


def get_csv_headers(csv_path: Path) -> list[str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return reader.fieldnames or []


def get_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def test_inventory_csv_has_headers():
    headers = get_csv_headers(USER_INVENTORY_CSV)

    assert len(headers) > 0


def test_intake_history_csv_has_headers():
    headers = get_csv_headers(USER_INTAKE_HISTORY_CSV)

    assert len(headers) > 0


def test_intake_items_csv_has_headers():
    headers = get_csv_headers(USER_INTAKE_ITEMS_CSV)

    assert len(headers) > 0


def test_inventory_csv_has_required_columns():
    headers = set(get_csv_headers(USER_INVENTORY_CSV))

    required_columns = {
        "stock_id",
        "food_item",
        "category",
    }

    missing_columns = required_columns - headers

    assert not missing_columns, f"Missing columns: {missing_columns}"


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
        "intake_id",
        "food_item",
    }

    missing_columns = required_columns - headers

    assert not missing_columns, f"Missing columns: {missing_columns}"


def test_data_descriptions_file_is_not_empty():
    text = DATA_DESCRIPTIONS_TXT.read_text(encoding="utf-8")

    assert len(text.strip()) > 0