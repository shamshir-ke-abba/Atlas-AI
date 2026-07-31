"""
Atlas AI V3

Entry Point
"""

from gui.app import AtlasApplication
from gui.window import AtlasWindow

from core.bus import EventBus
from core.state import AtlasState
from core.controller import Controller


def main():

    # -----------------------------------------
    # Core
    # -----------------------------------------

    bus = EventBus()

    state = AtlasState()

    controller = Controller(
        bus=bus,
        state=state,
    )

    # -----------------------------------------
    # GUI
    # -----------------------------------------

    app = AtlasApplication()

    window = AtlasWindow(
        bus=bus,
        state=state,
    )

    # -----------------------------------------
    # Start Services
    # -----------------------------------------

    controller.start()

    # -----------------------------------------
    # Show Window
    # -----------------------------------------

    window.show()

    app.exec()


if __name__ == "__main__":
    main()