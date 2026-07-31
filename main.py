"""
Atlas V3 Entry Point
"""

from core.bus import EventBus
from core.state import AtlasState
from core.controller import Controller

from gui.window import AtlasWindow


def main():

    # Create core services

    bus = EventBus()

    state = AtlasState()

    # Create controller

    controller = Controller(
        bus=bus,
        state=state,
    )

    # Create GUI

    window = AtlasWindow(
        bus=bus,
        state=state,
    )

    # Start Atlas

    controller.start()

    window.run()


if __name__ == "__main__":

    main()