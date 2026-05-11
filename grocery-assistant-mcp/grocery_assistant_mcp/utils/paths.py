from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent

DATA_DIR = PACKAGE_ROOT / "mcp_resources" / "data"
LOG_DIR = PROJECT_ROOT / "logs"

INVENTORY_PATH = DATA_DIR / "user_inventory.csv"
INTAKE_HISTORY_PATH = DATA_DIR / "user_intake_history.csv"
INTAKE_ITEMS_PATH = DATA_DIR / "user_intake_items.csv"
DATA_DESCRIPTIONS_PATH = DATA_DIR / "data_descriptions.txt"