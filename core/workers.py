"""
Atlas V3 Workers

Background workers for long-running tasks.
"""

from PySide6.QtCore import QObject, Signal, Slot

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

        print("\n========== AIWorker ==========")
        print("Worker started")
        print("Message:", message)

        try:

            for piece in self.brain.process(message):

                print("Chunk:", repr(piece))

                self.chunk.emit(
                    piece
                )

            print("Worker finished")

        except Exception as e:

            import traceback

            print("\n!!! AIWorker Exception !!!")
            traceback.print_exc()

        self.finished.emit()