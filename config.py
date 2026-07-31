"""
Atlas V3 Configuration

All configurable values for Atlas live here.
Nothing else in the project should contain
hardcoded paths or model names.
"""

from pathlib import Path

# ==========================================================
# Project Paths
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"
ASSET_DIR = ROOT_DIR / "assets"

MEMORY_FILE = DATA_DIR / "memory.json"
HISTORY_FILE = DATA_DIR / "history.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"

LOG_FILE = LOG_DIR / "atlas.log"

# ==========================================================
# AI Configuration
# ==========================================================

MODEL_NAME = "qwen2.5:1.5b"

OLLAMA_HOST = "http://localhost:11434"

TEMPERATURE = 0.2

MAX_HISTORY = 20

# ==========================================================
# GUI Configuration
# ==========================================================

WINDOW_TITLE = "Atlas AI V3"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

MIN_WIDTH = 900
MIN_HEIGHT = 600

# ==========================================================
# Memory Configuration
# ==========================================================

AUTO_SAVE_MEMORY = True

MAX_MEMORY_RESULTS = 10

# ==========================================================
# Logging
# ==========================================================

LOG_LEVEL = "INFO"