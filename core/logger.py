"""
Atlas V3 Logger

Central logging system used throughout Atlas.
"""

import logging

from config import (
    LOG_FILE,
    LOG_LEVEL,
    LOG_DIR,
)

# ----------------------------------------------------------
# Create logs directory
# ----------------------------------------------------------

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# ----------------------------------------------------------
# Logger
# ----------------------------------------------------------

logger = logging.getLogger("Atlas")

if not logger.handlers:

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)