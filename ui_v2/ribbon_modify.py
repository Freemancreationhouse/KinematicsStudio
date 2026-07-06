from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)


class ModifyRibbon(QWidget):
    """Ribbon section for modify and view maintenance commands."""

    BUTTONS = [
        "Move",
        "Undo",
        "Redo",
        "Fit View",
        "Zoom Extents",
        "Copy",
        "Array",
        "Rotate",
        "Scale",
        "Mirror",
        "Trim",
        "Offset",
        "Extend",
        "Fillet",
        "Chamfer"
    ]

    def __init__(self, tool_manager):

        super().__init__()

        self.tool_manager = tool_manager

        layout = QGridLayout(self)

        self._build_buttons(layout)

    # ---------------------------------------------

    def _build_buttons(self, layout):

        row = 0
        col = 0

        for text in self.BUTTONS:
            button = self._button(text)
            layout.addWidget(button, row, col)

            col += 1

            if col == 3:
                col = 0
                row += 1

        layout.setRowStretch(row + 1, 1)

    # ---------------------------------------------

    def _button(self, text):

        button = QPushButton(text)
        button.setMinimumHeight(42)
        self._connect_button(button, text)
        return button

    # ---------------------------------------------

    def _connect_button(self, button, text):

        if text == "Move":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("MoveTool")
            )
        elif text == "Trim":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("TrimTool")
            )
        elif text == "Extend":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("ExtendTool")
            )
        elif text == "Offset":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("OffsetTool")
            )
        elif text == "Copy":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("CopyTool")
            )
        elif text == "Array":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("ArrayTool")
            )
        elif text == "Fillet":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("FilletTool")
            )
        elif text == "Chamfer":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("ChamferTool")
            )
        elif text == "Rotate":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("RotateTool")
            )
        elif text == "Mirror":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("MirrorTool")
            )
        elif text == "Scale":
            button.clicked.connect(
                lambda checked=False: self.tool_manager.activate("ScaleTool")
            )
        elif text == "Undo":
            button.clicked.connect(self._undo)
        elif text == "Redo":
            button.clicked.connect(self._redo)
        elif text == "Fit View":
            button.clicked.connect(self._fit_view)
        elif text == "Zoom Extents":
            button.clicked.connect(self._zoom_extents)

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
