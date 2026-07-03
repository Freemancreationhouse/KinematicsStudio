from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)


class AIRibbon(QWidget):

    def __init__(self):

        super().__init__()

        layout = QGridLayout(self)

        buttons = [

            "AI Chat",
            "Text → CAD",
            "Sketch → CAD",
            "Image → CAD",
            "Image → 3D",
            "Photo → Mesh",
            "Floor Plan",
            "Render AI",
            "AI Assistant"

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