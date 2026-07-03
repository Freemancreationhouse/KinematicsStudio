from PySide6.QtWidgets import (
    QStatusBar,
    QLabel,
)


class StudioStatusBar(QStatusBar):

    def __init__(self):

        super().__init__()

        self.coords = QLabel("X:0  Y:0")

        self.snap = QLabel("Snap: OFF")

        self.tool = QLabel("Tool: Select")

        self.machine = QLabel("Machine: Disconnected")

        self.addPermanentWidget(self.coords)

        self.addPermanentWidget(self.snap)

        self.addPermanentWidget(self.tool)

        self.addPermanentWidget(self.machine)