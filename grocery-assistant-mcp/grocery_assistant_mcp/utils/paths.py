from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PACKAGE_ROOT = PROJECT_ROOT / "grocery_mcp"

MCP_RESOURCES_DIR = PACKAGE_ROOT / "mcp_resources"
MCP_RESOURCE_DATA_DIR = MCP_RESOURCES_DIR / "data"

LOG_DIR = PROJECT_ROOT / "logs"

INVENTORY_PATH = MCP_RESOURCE_DATA_DIR / "user_inventory.csv"
INTAKE_HISTORY_PATH = MCP_RESOURCE_DATA_DIR / "user_intake_history.csv"
INTAKE_ITEMS_PATH = MCP_RESOURCE_DATA_DIR / "user_intake_items.csv"

APP_LOG_PATH = LOG_DIR / "grocery_mcp.log"