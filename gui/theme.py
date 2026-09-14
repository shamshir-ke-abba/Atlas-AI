"""
Atlas V3 Theme Tokens & Constants.

Canonical implementation conforming to docs/design/ATLAS_DESIGN_SYSTEM_V1.md.
Provides design tokens for native PySide6 desktop interface.
"""

from __future__ import annotations

# ==============================================================================
# 1. CANONICAL DARK THEME TOKENS (DEFAULT)
# ==============================================================================

BG_BASE = "#09090B"
BG_SURFACE = "#121215"
BG_ELEVATED = "#1C1C22"

BORDER_SUBTLE = "#27272F"
BORDER_STRONG = "#3F3F4A"

TEXT_PRIMARY = "#F4F4F5"
TEXT_SECONDARY = "#A1A1AA"
TEXT_MUTED = "#82828C"

BRAND_UI = "#398C8F"
BRAND_TEXT = "#4FB8BA"

SEMANTIC_SUCCESS = "#4ADE80"
SEMANTIC_WARNING = "#FBBF24"
SEMANTIC_ERROR = "#F87171"
SEMANTIC_INFO = "#60A5FA"

# ==============================================================================
# 2. CANONICAL LIGHT THEME TOKENS
# ==============================================================================

LIGHT_BG_BASE = "#F4F4F5"
LIGHT_BG_SURFACE = "#FFFFFF"
LIGHT_BG_ELEVATED = "#E4E4E7"

LIGHT_BORDER_SUBTLE = "#E4E4E7"
LIGHT_BORDER_STRONG = "#D4D4D8"

LIGHT_TEXT_PRIMARY = "#09090B"
LIGHT_TEXT_SECONDARY = "#52525B"
LIGHT_TEXT_MUTED = "#71717A"

LIGHT_BRAND_UI = "#2A7376"
LIGHT_BRAND_TEXT = "#1D5355"

LIGHT_SEMANTIC_SUCCESS = "#16A34A"
LIGHT_SEMANTIC_WARNING = "#D97706"
LIGHT_SEMANTIC_ERROR = "#DC2626"
LIGHT_SEMANTIC_INFO = "#2563EB"

# ==============================================================================
# 3. TYPOGRAPHY
# ==============================================================================

FONT_FAMILY = "Inter, 'Segoe UI', -apple-system, Roboto, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Consolas', 'Courier New', monospace"

FONT_DISPLAY = 24
FONT_H1 = 18
FONT_H2 = 16
FONT_SUBHEADING = 16
FONT_BODY = 14
FONT_SMALL = 13
FONT_CAPTION = 12
FONT_CODE = 13

# ==============================================================================
# 4. SPACING & RADII (4px BASELINE)
# ==============================================================================

SPACE_4 = 4
SPACE_8 = 8
SPACE_12 = 12
SPACE_16 = 16
SPACE_24 = 24
SPACE_32 = 32
SPACE_48 = 48
SPACE_64 = 64

RADIUS_SM = 4
RADIUS_MD = 6
RADIUS_LG = 8

# ==============================================================================
# 5. BACKWARD-COMPATIBLE ALIASES
# ==============================================================================

BACKGROUND = BG_BASE
PANEL = BG_SURFACE
CARD = BG_ELEVATED

TEXT = TEXT_PRIMARY
SECONDARY = TEXT_SECONDARY
MUTED = TEXT_MUTED

ACCENT = BRAND_UI
BUTTON = BRAND_UI
BUTTON_HOVER = BRAND_TEXT

SUCCESS = SEMANTIC_SUCCESS
WARNING = SEMANTIC_WARNING
ERROR = SEMANTIC_ERROR
INFO = SEMANTIC_INFO

FONT = "Inter"
FONT_SIZE = FONT_BODY
TITLE_SIZE = FONT_H1
HEADER_SIZE = FONT_DISPLAY


# ==============================================================================
# 6. ACCESSIBILITY & PREFERENCES
# ==============================================================================

def is_reduced_motion() -> bool:
    """Return True if the user has requested reduced motion."""
    try:
        from PySide6.QtCore import QSettings
        settings = QSettings("AtlasAI", "AtlasV3")
        return bool(settings.value("reduced_motion", False, type=bool))
    except Exception:
        return False


def set_reduced_motion(enabled: bool) -> None:
    """Persist reduced motion preference."""
    try:
        from PySide6.QtCore import QSettings
        settings = QSettings("AtlasAI", "AtlasV3")
        settings.setValue("reduced_motion", bool(enabled))
    except Exception:
        pass