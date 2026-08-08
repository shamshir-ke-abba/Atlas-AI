"""
Atlas V3
Main Application Entry Point
"""

import sys

from core.bus import EventBus
from core.controller import Controller
from core.logger import logger
from core.state import AtlasState

from gui.app import AtlasApplication
from gui.window import AtlasWindow


def main():

    logger.info(
        "Atlas GUI starting..."
    )

    # -----------------------------------------
    # Core Runtime
    # -----------------------------------------

    bus = EventBus()
    state = AtlasState()

    logger.info(
        "Core runtime loaded."
    )

    # -----------------------------------------
    # GUI
    # -----------------------------------------

    app = AtlasApplication()

    logger.info(
        "Atlas application created."
    )

    # -----------------------------------------
    # Controller
    # -----------------------------------------

    controller = Controller(
        bus=bus,
        state=state,
    )

    # -----------------------------------------
    # Main Window
    # -----------------------------------------

    window = AtlasWindow(
        bus=bus,
        state=state,
        controller=controller,
    )

    logger.info(
        "Atlas main window created."
    )

    # -----------------------------------------
    # Start Services
    # -----------------------------------------

    controller.start()

    logger.info(
        "Atlas controller started."
    )

    # -----------------------------------------
    # Show GUI
    # -----------------------------------------

    window.show()

    logger.info(
        "Atlas GUI started successfully."
    )

    # -----------------------------------------
    # Qt Event Loop
    # -----------------------------------------

    exit_code = app.exec()

    # -----------------------------------------
    # Shutdown
    # -----------------------------------------

    logger.info(
        f"Atlas GUI exited with code {exit_code}."
    )

    controller.stop()

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()