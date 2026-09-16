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
    generation_id: str | None = None


@dataclass(slots=True)
class ThinkingFinished(Event):
    generation_id: str | None = None


@dataclass(slots=True)
class ChunkReceived(Event):
    text: str
    generation_id: str | None = None


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


@dataclass(slots=True)
class ProfileSetupRequested(Event):
    """Ask the GUI to display an interactive tool profile form."""
    tool: str
    prompt: str = ""


@dataclass(slots=True)
class ProfileSetupCompleted(Event):
    """Published after a profile form is saved."""
    tool: str
    profile: dict
    message: str = ""


# ==========================================================
# Error Events
# ==========================================================

@dataclass(slots=True)
class ErrorOccurred(Event):
    message: str
    generation_id: str | None = None
