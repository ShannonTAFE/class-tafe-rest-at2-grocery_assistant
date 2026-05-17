from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "grocery_assistant_mcp"

DATA_DIR = PACKAGE_ROOT / "mcp_resources" / "data"
LOG_DIR = PROJECT_ROOT / "logs"

USER_INVENTORY_CSV = DATA_DIR / "user_inventory.csv"
USER_INTAKE_HISTORY_CSV = DATA_DIR / "user_intake_history.csv"
USER_INTAKE_ITEMS_CSV = DATA_DIR / "user_intake_items.csv"
USER_INVENTORY_CONSUMPTION_CSV = DATA_DIR / "user_inventory_consumption.csv"
DATA_DESCRIPTIONS_TXT = DATA_DIR / "data_descriptions.txt"
FOOD_WASTE_PATH_CSV = DATA_DIR / "user_food_waste.csv"


def test_project_root_exists():
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()


def test_package_root_exists():
    assert PACKAGE_ROOT.exists()
    assert PACKAGE_ROOT.is_dir()


def test_data_directory_exists():
    assert DATA_DIR.exists()
    assert DATA_DIR.is_dir()


def test_logs_directory_exists():
    assert LOG_DIR.exists()
    assert LOG_DIR.is_dir()


def test_expected_resource_files_exist():
    assert USER_INVENTORY_CSV.exists()
    assert USER_INTAKE_HISTORY_CSV.exists()
    assert USER_INTAKE_ITEMS_CSV.exists()
    assert USER_INVENTORY_CONSUMPTION_CSV.exists()
    assert DATA_DESCRIPTIONS_TXT.exists()
    assert FOOD_WASTE_PATH_CSV.exists()
