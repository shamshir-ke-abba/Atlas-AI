"""
gui/app.py

Creates the Qt Application.
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


class AtlasApplication(QApplication):
    """
    Atlas Qt Application.
    """

    def __init__(self):

        super().__init__(sys.argv)

        self.setApplicationName("Atlas AI")
        self.setApplicationVersion("3.0")
        self.setOrganizationName("Atlas")

        self.load_stylesheet()

    # =====================================================
    # Styles
    # =====================================================

    def load_stylesheet(self):

        style_path = (
            Path(__file__).parent
            / "styles"
            / "atlas.qss"
        )

        if style_path.exists():

            with open(style_path, "r") as file:

                self.setStyleSheet(
                    file.read()
                )