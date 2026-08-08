"""
Atlas Memory Patterns
"""

PATTERNS = [

    ("my name is", "identity", "name"),
    ("i am", "identity", "name"),
    ("mera naam", "identity", "name"),  # Hindi: My name
    ("main", "identity", "name"),       # Hindi: I am

    ("i live in", "identity", "city"),
    ("mujhe ghar", "identity", "city"), # Hindi: My home

    ("my favorite food is", "preferences", "favorite_food"),
    ("my favourite food is", "preferences", "favorite_food"),
    ("mera pasand", "preferences", "favorite_food"),  # Hindi: My preference

    ("my favorite color is", "preferences", "favorite_color"),
    ("my favourite color is", "preferences", "favorite_color"),
    ("mera pasand rang", "preferences", "favorite_color"),  # Hindi: My favorite color

]