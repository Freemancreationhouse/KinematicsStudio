from PySide6.QtWidgets import (
    QGridLayout,
    QPushButton,
    QWidget,
)


class BlocksRibbon(QWidget):
    """Ribbon section for block workflows."""

    BUTTONS = [
        ("Insert", "InsertBlockTool"),
        ("Explode", "ExplodeBlockTool"),
    ]

    def __init__(self, tool_manager):

        super().__init__()
        self.tool_manager = tool_manager

        layout = QGridLayout(self)

        for column, (text, tool) in enumerate(self.BUTTONS):
            button = QPushButton(text)
            button.setMinimumHeight(42)
            button.setToolTip(f"Activate {text}.")
            button.clicked.connect(
                lambda checked=False, name=tool: self.tool_manager.activate(name)
            )
            layout.addWidget(button, 0, column)

        layout.setRowStretch(1, 1)
