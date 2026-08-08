"""
Atlas AI V3

Entry Point
"""

from gui.app import AtlasApplication
from gui.window import AtlasWindow

from core.logger import get_logger

from core.runtime import (
    bus,
    state,
    controller,
)


logger = get_logger("gui")


def main():

    logger.info(
        "Atlas GUI starting..."
    )

    try:

        # -----------------------------------------
        # Core
        # -----------------------------------------

        # Runtime already created the shared:
        # - EventBus
        # - AtlasState
        # - Controller

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
        # Show Window
        # -----------------------------------------

        window.show()

        logger.info(
            "Atlas GUI started successfully."
        )

        exit_code = app.exec()

        logger.info(
            "Atlas GUI exited with code %s.",
            exit_code,
        )

        return exit_code

    except Exception:

        logger.exception(
            "Fatal GUI error."
        )

        raise


if __name__ == "__main__":
    main()