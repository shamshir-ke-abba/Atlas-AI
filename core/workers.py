"""
Atlas V3 Workers

Background workers for long-running tasks.
"""

from PySide6.QtCore import QObject, Signal, Slot

from ai.brain import AtlasBrain


class AIWorker(QObject):

    finished = Signal(str)

    def __init__(self):

        super().__init__()

        self.brain = AtlasBrain()

    @Slot(str)
    def process(
        self,
        message
    ):

        response = self.brain.process(
            message
        )

        self.finished.emit(
            response
        )