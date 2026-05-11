import logging
from logging.handlers import RotatingFileHandler

from grocery_assistant_mcp.utils.paths import LOG_DIR


def configure_logging() -> None:
    """
    Configure file-based logging for the MCP server.

    Important:
    Avoid logging to stdout for stdio MCP servers because stdout is used
    for MCP JSON-RPC communication.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return

    log_file = LOG_DIR / "mcp_v1.log"
    error_log_file = LOG_DIR / "mcp_v1_errors.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    app_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)

    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(app_handler)
    logger.addHandler(error_handler)

    logging.getLogger(__name__).info("Logging configured")