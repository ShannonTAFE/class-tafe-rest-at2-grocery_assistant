import logging

from grocery_assistant_mcp.core.grocery_service import read_csv_file
from grocery_assistant_mcp.utils.logging_config import configure_logging
from grocery_assistant_mcp.utils.paths import LOG_DIR


def test_configure_logging_runs_without_error():
    configure_logging()

    assert LOG_DIR.exists()
    assert LOG_DIR.is_dir()


def test_configure_logging_creates_file_handlers():
    configure_logging()

    root_logger = logging.getLogger()

    file_handlers = [
        handler
        for handler in root_logger.handlers
        if hasattr(handler, "baseFilename")
    ]

    assert len(file_handlers) >= 1


def test_missing_csv_file_logs_warning(tmp_path, caplog):
    missing_csv = tmp_path / "missing.csv"

    with caplog.at_level(logging.WARNING, logger="grocery_mcp.grocery_data"):
        df = read_csv_file(missing_csv)

    assert df.empty
    assert "CSV file not found" in caplog.text