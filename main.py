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

    # ==================================================
    # CORE
    # ==================================================

    bus = EventBus()

    state = AtlasState()

    logger.info(
        "Core runtime loaded."
    )

    # ==================================================
    # QT APPLICATION
    # ==================================================

    app = AtlasApplication()

    logger.info(
        "Atlas application created."
    )

    # ==================================================
    # CONTROLLER
    # ==================================================

    controller = Controller(
        bus=bus,
        state=state,
    )

    # ==================================================
    # MAIN WINDOW
    # ==================================================

    window = AtlasWindow(
        bus=bus,
        state=state,
        controller=controller,
    )

    controller.set_gui_parent(window)

    logger.info(
        "Atlas main window created."
    )

    # ==================================================
    # START BACKEND
    # ==================================================

    controller.start()

    # ==================================================
    # SHOW GUI
    # ==================================================

    window.show()

    logger.info(
        "Atlas GUI started successfully."
    )

    # ==================================================
    # EVENT LOOP
    # ==================================================

    exit_code = app.exec()

    # ==================================================
    # SHUTDOWN
    # ==================================================

    controller.stop()

    logger.info(
        "Atlas GUI exited with code %s",
        exit_code,
    )

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()