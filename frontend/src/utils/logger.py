# src/utils/logger.py
"""
Minimal logger for the Streamlit application.

Usage:
    from utils.logger import configure_logging, get_logger

    configure_logging()
    logger = get_logger(__name__)
    logger.info("Logging is active")
"""

import logging
from logging.handlers import RotatingFileHandler
from os import makedirs, path


def configure_logging(settings):
    """
    Configure global logging for the ui.

    Args:
        settings: Application settings containing log_file_name, log_level, and console_handler attributes.
    """
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        # Avoid re-adding handlers if already configured
        return

    # Prepare file path (optional: allow directory structure in log_file_name)
    log_file_name = settings.log_file_name
    log_dir = getattr(
        settings, "log_dir_name", "."
    )  # Default to current dir if not set
    log_file = (
        log_file_name if log_file_name.endswith(".log") else f"{log_file_name}.log"
    )
    log_path = path.join(log_dir, log_file)

    makedirs(log_dir, exist_ok=True)

    # Determine log level
    log_level_name = settings.log_level.upper()
    valid_levels = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
    if log_level_name not in valid_levels:
        log_level_name = "INFO"
        logging.basicConfig(level=logging.INFO)
        logging.warning(f"Invalid LOG_LEVEL '{log_level_name}', defaulting to INFO.")
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Rotating file handler
    file_handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    )
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Console handler
    if settings.console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        root_logger.addHandler(console_handler)
        root_logger.info("Console logging enabled.")

    root_logger.info(
        f"Logging initialized (console={log_level_name}, file=DEBUG at {log_path})"
    )


def get_logger(name):
    """
    Get a logger for a specific component.

    Args:
        name (str): Logger name, usually __name__ of the module.

    Returns:
        logging.Logger: Logger instance.
    """
    return logging.getLogger(name)
