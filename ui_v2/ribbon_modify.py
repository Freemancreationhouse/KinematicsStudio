from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)


class ModifyRibbon(QWidget):

    def __init__(self, tool_manager):

        super().__init__()

        self.tool_manager = tool_manager

        layout = QGridLayout(self)

        buttons = [

            "Move",
            "Copy",
            "Rotate",
            "Scale",
            "Mirror",
            "Trim",
            "Offset",
            "Extend",
            "Fillet"

        ]

        row = 0
        col = 0

        for text in buttons:

            b = QPushButton(text)

            b.setMinimumHeight(42)

            layout.addWidget(

                b,

                row,

                col

            )

            col += 1

            if col == 3:

                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)