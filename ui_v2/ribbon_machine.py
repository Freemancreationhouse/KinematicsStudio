from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)


class MachineRibbon(QWidget):

    def __init__(self):

        super().__init__()

        layout = QGridLayout(self)

        buttons = [

            "Connect",
            "Disconnect",
            "Home",
            "Unlock",
            "Jog",
            "Zero",
            "Send GCode",
            "Laser",
            "3D Printer",
            "CNC",
            "Camera",
            "Settings"

        ]

        row = 0
        col = 0

        for text in buttons:

            button = QPushButton(text)

            button.setMinimumHeight(42)

            layout.addWidget(

                button,

                row,

                col

            )

            col += 1

            if col == 3:

                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)