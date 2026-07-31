"""
Atlas V3 Exceptions

Custom exception hierarchy for Atlas.
"""


class AtlasError(Exception):
    """Base exception for all Atlas errors."""
    pass


class ModelError(AtlasError):
    """Raised when the AI model fails."""
    pass


class ToolError(AtlasError):
    """Raised when a tool fails."""
    pass


class MemoryError(AtlasError):
    """Raised when memory operations fail."""
    pass


class KnowledgeError(AtlasError):
    """Raised when knowledge operations fail."""
    pass


class ConfigurationError(AtlasError):
    """Raised when configuration is invalid."""
    pass