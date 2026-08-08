"""
Atlas V3 Runtime

Creates the shared runtime objects used by
the GUI and web interface.
"""

from core.bus import EventBus
from core.controller import Controller
from core.state import AtlasState


bus = EventBus()

state = AtlasState()

controller = Controller(
    bus=bus,
    state=state,
)