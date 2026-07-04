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
            "Undo",
            "Redo",
            "Fit View",
            "Zoom Extents",
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

            if text == "Move":
                b.clicked.connect(
                    lambda checked=False: self.tool_manager.activate("MoveTool")
                )
            elif text == "Undo":
                b.clicked.connect(self._undo)
            elif text == "Redo":
                b.clicked.connect(self._redo)
            elif text == "Fit View":
                b.clicked.connect(self._fit_view)
            elif text == "Zoom Extents":
                b.clicked.connect(self._zoom_extents)

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

    # ---------------------------------------------

    def _undo(self):

        workspace = self._workspace()

        if workspace:
            workspace.command_manager.undo()

    # ---------------------------------------------

    def _redo(self):

        workspace = self._workspace()

        if workspace:
            workspace.command_manager.redo()

    # ---------------------------------------------

    def _workspace(self):

        app = getattr(self.tool_manager, "app", None)

        return getattr(app, "workspace", None)

    # ---------------------------------------------

    def _fit_view(self):

        canvas = getattr(self.tool_manager, "canvas", None)

        if canvas:
            canvas.fit_view()

    # ---------------------------------------------

    def _zoom_extents(self):

        canvas = getattr(self.tool_manager, "canvas", None)

        if canvas:
            canvas.zoom_extents()
