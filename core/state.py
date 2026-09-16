"""
Atlas V3 Application State

Stores the runtime state shared across Atlas.
"""

from dataclasses import dataclass, field
from threading import Event
from typing import Optional


@dataclass
class AtlasState:
    """
    Shared runtime state.
    """

    # ------------------------------------------------------
    # AI
    # ------------------------------------------------------

    is_generating: bool = False

    active_generation_id: Optional[str] = None

    stop_event: Event = field(
        default_factory=Event
    )

    # ------------------------------------------------------
    # Conversation
    # ------------------------------------------------------

    active_conversation_id: Optional[str] = None

    current_message: str = ""

    current_response: str = ""

    # ------------------------------------------------------
    # Model
    # ------------------------------------------------------

    model_loaded: bool = False

    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------

    status: str = "Idle"