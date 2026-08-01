"""
Atlas V3 Events

Every component communicates by publishing
and subscribing to events.
"""

from dataclasses import dataclass
from typing import Any


# ==========================================================
# Base Event
# ==========================================================

@dataclass(slots=True)
class Event:
    """Base class for all events."""
    pass


# ==========================================================
# Chat Events
# ==========================================================

@dataclass(slots=True)
class ConversationCleared(Event):
    pass

@dataclass(slots=True)
class MessageReceived(Event):
    text: str


@dataclass(slots=True)
class ThinkingStarted(Event):
    pass


@dataclass(slots=True)
class ThinkingFinished(Event):
    pass


@dataclass(slots=True)
class ChunkReceived(Event):
    text: str


# ==========================================================
# Tool Events
# ==========================================================

@dataclass(slots=True)
class ToolRequested(Event):
    tool: str
    arguments: dict


@dataclass(slots=True)
class ToolFinished(Event):
    tool: str
    result: Any


# ==========================================================
# Error Events
# ==========================================================

@dataclass(slots=True)
class ErrorOccurred(Event):
    message: str