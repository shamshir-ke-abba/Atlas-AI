"""
gui/widgets/statusbar.py

Atlas Status Widget.
"""

from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.events import (
    ThinkingStarted,
    ThinkingFinished,
)


class AtlasStatusBar(QWidget):

    def __init__(
        self,
        bus,
        parent=None
    ):

        super().__init__(parent)

        self.bus = bus

        self.bus.subscribe(
            ThinkingStarted,
            self.thinking_started
        )

        self.bus.subscribe(
            ThinkingFinished,
            self.thinking_finished
        )

        self.setObjectName("StatusBar")

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

        title = QLabel("Atlas Status")

        title.setObjectName("StatusTitle")

        layout.addWidget(title)

        self.state_label = QLabel(
            "State: Ready"
        )

        self.state_label.setObjectName(
            "StatusText"
        )

        layout.addWidget(
            self.state_label
        )

        layout.addStretch()

    # =====================================================
    # Events
    # =====================================================

    def thinking_started(
        self,
        event
    ):

        self.state_label.setText(
            "State: Thinking..."
        )

    print("Thinking Finished Event Received")

    def thinking_finished(
        self,
        event
    ):

        self.state_label.setText(
            "State: Ready"
        )