"""
Atlas Memory Patterns
"""

PATTERNS = [

    # ==================================================
    # Identity
    # ==================================================

    (
        r"\bmy name is\s+(.+?)(?:\s+and\b|[.!?,]|$)",
        "identity",
        "name",
    ),

    (
        r"\bi am\s+([A-Za-z][A-Za-z0-9_-]*)(?:\s+and\b|[.!?,]|$)",
        "identity",
        "name",
    ),

    (
        r"\bmera naam\s+(.+?)(?:\s+hai\b|[.!?,]|$)",
        "identity",
        "name",
    ),

    # ==================================================
    # Location
    # ==================================================

    (
        r"\bi live in\s+(.+?)(?:\s+and\b|[.!?,]|$)",
        "identity",
        "city",
    ),

    (
        r"\bmujhe ghar\s+(.+?)(?:\s+hai\b|[.!?,]|$)",
        "identity",
        "city",
    ),

    # ==================================================
    # Food
    # ==================================================

    (
        r"\bmy favorite food is\s+(.+?)(?:\s+and\b|[.!?,]|$)",
        "preferences",
        "favorite_food",
    ),

    (
        r"\bmy favourite food is\s+(.+?)(?:\s+and\b|[.!?,]|$)",
        "preferences",
        "favorite_food",
    ),

    (
        r"\bmera pasand\s+(.+?)(?:\s+hai\b|[.!?,]|$)",
        "preferences",
        "favorite_food",
    ),

    # ==================================================
    # Color
    # ==================================================

    (
        r"\bmy favorite color is\s+(.+?)(?:\s+and\b|[.!?,]|$)",
        "preferences",
        "favorite_color",
    ),

    (
        r"\bmy favourite color is\s+(.+?)(?:\s+and\b|[.!?,]|$)",
        "preferences",
        "favorite_color",
    ),

    (
        r"\bmera pasand rang\s+(.+?)(?:\s+hai\b|[.!?,]|$)",
        "preferences",
        "favorite_color",
    ),
]