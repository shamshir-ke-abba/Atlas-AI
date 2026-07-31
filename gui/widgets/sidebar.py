"""
gui/widgets/sidebar.py

Atlas Sidebar Widget.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)


class AtlasSidebar(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setObjectName("Sidebar")

        self.build_ui()


    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        title = QLabel("Atlas AI")

        title.setObjectName("SidebarTitle")

        layout.addWidget(title)

        layout.addStretch()