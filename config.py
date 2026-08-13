"""
AtlasAI V3 Configuration
"""

from pathlib import Path

# =============================================
# Paths
# =============================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
MEMORY_FILE = DATA_DIR / "memory.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge.json"
HISTORY_FILE = DATA_DIR / "history.json"
LOGS_DIR = PROJECT_ROOT / "logs"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Create directories if they don't exist
for directory in [DATA_DIR, CONVERSATIONS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================
# Model Configuration
# =============================================

MODEL_NAME = "qwen2.5:1.5b"
OLLAMA_HOST = "http://localhost:11434"
TEMPERATURE = 0.2
MAX_HISTORY = 20
MAX_TOKENS = 512

# =============================================
# Web Server Configuration
# =============================================

WEB_HOST = "0.0.0.0"
WEB_PORT = 8000
WEB_DEBUG = False

# =============================================
# GUI Configuration
# =============================================

GUI_WINDOW_WIDTH = 1200
GUI_WINDOW_HEIGHT = 800
GUI_THEME = "dark"

# =============================================
# Feature Flags
# =============================================

ENABLE_VOICE = False
ENABLE_WEB_RESEARCH = True
ENABLE_TOOLS = True
ENABLE_MEMORY = True

# =============================================
# Logging
# =============================================

LOG_FILE = LOGS_DIR / "atlas.log"
LOG_LEVEL = "INFO"