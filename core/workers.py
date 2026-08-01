"""
Atlas V3 Workers

Background workers for long-running tasks.
"""

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)

from ai.brain import AtlasBrain


class AIWorker(QObject):

    chunk = Signal(str)
    finished = Signal()

    def __init__(self):

        super().__init__()

        self.brain = AtlasBrain()

    @Slot(str)
    def process(
        self,
        message,
    ):

        for piece in self.brain.process(
            message,
        ):

            self.chunk.emit(
                piece,
            )

        self.finished.emit()