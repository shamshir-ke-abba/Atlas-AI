from PySide6.QtCore import QObject, Signal


class ControllerSignals(QObject):

    ai_response = Signal(str)

    def __init__(self):

        super().__init__()