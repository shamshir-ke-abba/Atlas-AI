"""
gui/app.py

Creates the Atlas Qt Application.
"""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


class AtlasApplication(QApplication):

    def __init__(self):

        super().__init__(
            sys.argv
        )

        self.setApplicationName(
            "Atlas AI"
        )

        self.setApplicationVersion(
            "3.0"
        )

        self.setOrganizationName(
            "Atlas"
        )

        icon_path = (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "atlas_favicon.svg"
        )
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.load_stylesheet()

    # ==================================================
    # STYLES
    # ==================================================

    def load_stylesheet(self):

        style_path = (
            Path(__file__).parent
            / "styles"
            / "atlas.qss"
        )

        if style_path.exists():

            with open(
                style_path,
                "r",
                encoding="utf-8",
            ) as file:

                self.setStyleSheet(
                    file.read()
                )