"""
Atlas V3 Logging System

Centralized logging for the Atlas runtime,
web interface, and GUI.
"""

import logging
from logging.handlers import RotatingFileHandler

from config import LOG_FILE


LOG_DIR = LOG_FILE.parent

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def get_logger(name="atlas"):

    logger = logging.getLogger(name)

    # Prevent duplicate handlers if this module
    # is imported multiple times.
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    logger.propagate = False

    formatter = logging.Formatter(
        LOG_FORMAT
    )

    # --------------------------------------------------
    # File Handler
    # --------------------------------------------------

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    # --------------------------------------------------
    # Console Handler
    # --------------------------------------------------

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    return logger


logger = get_logger("atlas")