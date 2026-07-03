from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
)


class CommandBar(QWidget):

    def __init__(self):

        super().__init__()

        layout = QHBoxLayout(self)

        layout.addWidget(

            QLabel("Command")

        )

        self.command = QLineEdit()

        self.command.setPlaceholderText(

            "Type a command..."

        )

        layout.addWidget(

            self.command
        )