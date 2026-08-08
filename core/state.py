"""
Atlas V3 Application State

Stores the runtime state shared across Atlas.
"""

from dataclasses import dataclass, field
from threading import Event


@dataclass
class AtlasState:
    """
    Shared runtime state.
    """

    # --------------------------------------------------
    # AI
    # --------------------------------------------------

    is_generating: bool = False

    stop_event: Event = field(
        default_factory=Event
    )

    # --------------------------------------------------
    # Conversation
    # --------------------------------------------------

    current_message: str = ""

    current_response: str = ""

    # --------------------------------------------------
    # Model
    # --------------------------------------------------

    model_loaded: bool = False

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    status: str = "Idle"


# ======================================================
# Global State Instance
# ======================================================

state = AtlasState()