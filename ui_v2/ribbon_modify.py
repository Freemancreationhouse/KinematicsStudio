from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QPushButton,
)

from engine.commands.occ_boolean_command import OCCBooleanCommand


class ModifyRibbon(QWidget):
    """Ribbon section for modify and view maintenance commands."""

    BUTTONS = [
        "Move",
        "Undo",
        "Redo",
        "Fit View",
        "Zoom Extents",
        "2D View",
        "3D View",
        "Copy",
        "Array",
        "Rotate",
        "Scale",
        "Mirror",
        "Trim",
        "Offset",
        "Extend",
        "Fillet",
        "Chamfer",
        "Union",
        "Subtract",
        "Intersect",
        "Cube 3D",
        "Box 3D",
        "Plane 3D",
        "Cylinder 3D",
        "Cone 3D",
        "Sphere 3D",
        "Torus 3D",
        "Pyramid 3D",
        "Prism 3D",
        "Capsule 3D",
        "Extrude",
        "Revolve",
        "Sweep",
        "Loft",
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
        button.setToolTip(self._tooltip(text))
        self._connect_button(button, text)
        return button

    # ---------------------------------------------

    def _tooltip(self, text):

        shortcuts = {
            "Undo": "Undo the previous command (Ctrl+Z).",
            "Redo": "Redo the next command (Ctrl+Y).",
            "Fit View": "Fit the visible drawing in the canvas.",
            "Zoom Extents": "Zoom to the full drawing extents.",
            "2D View": "Switch to the existing 2D drawing canvas.",
            "3D View": "Switch to the 3D foundation viewport.",
        }

        return shortcuts.get(text, f"Activate {text}.")

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
        elif text == "Union":
            button.clicked.connect(lambda checked=False: self._boolean("union"))
        elif text == "Subtract":
            button.clicked.connect(lambda checked=False: self._boolean("subtract"))
        elif text == "Intersect":
            button.clicked.connect(lambda checked=False: self._boolean("intersect"))
        elif text == "Undo":
            button.clicked.connect(self._undo)
        elif text == "Redo":
            button.clicked.connect(self._redo)
        elif text == "Fit View":
            button.clicked.connect(self._fit_view)
        elif text == "Zoom Extents":
            button.clicked.connect(self._zoom_extents)
        elif text == "2D View":
            button.clicked.connect(self._show_2d_view)
        elif text == "3D View":
            button.clicked.connect(self._show_3d_view)
        elif text in self._primitive_tool_names():
            button.clicked.connect(
                lambda checked=False, tool=self._primitive_tool_names()[text]:
                    self.tool_manager.activate(tool)
            )
        elif text in self._solid_tool_names():
            button.clicked.connect(
                lambda checked=False, tool=self._solid_tool_names()[text]:
                    self.tool_manager.activate(tool)
            )

    # ---------------------------------------------

    def _primitive_tool_names(self):

        return {
            "Cube 3D": "CubePrimitiveTool",
            "Box 3D": "BoxPrimitiveTool",
            "Plane 3D": "PlanePrimitiveTool",
            "Cylinder 3D": "CylinderPrimitiveTool",
            "Cone 3D": "ConePrimitiveTool",
            "Sphere 3D": "SpherePrimitiveTool",
            "Torus 3D": "TorusPrimitiveTool",
            "Pyramid 3D": "PyramidPrimitiveTool",
            "Prism 3D": "PrismPrimitiveTool",
            "Capsule 3D": "CapsulePrimitiveTool",
        }

    # ---------------------------------------------

    def _solid_tool_names(self):

        return {
            "Extrude": "ExtrudeTool",
            "Revolve": "RevolveTool",
            "Sweep": "SweepTool",
            "Loft": "LoftTool",
        }

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

    def _boolean(self, operation):

        app = getattr(self.tool_manager, "app", None)
        workspace = self._workspace()
        engine = getattr(app, "engine", None)

        if app is None or workspace is None or engine is None:
            return

        shapes = getattr(getattr(engine, "occ", None), "shapes", [])
        selected = [
            item for item in list(workspace.selection.selected)
            if item in shapes
        ]

        if len(selected) != 2:
            self._show_status_text("Select exactly two OCC solids for Boolean operation.")
            return

        try:
            workspace.command_manager.execute(
                OCCBooleanCommand(engine, workspace, operation, selected[0], selected[1])
            )
        except Exception as error:
            self._show_status_text(f"Boolean {operation} failed: {error}")
            return

        self._show_status_text(f"Boolean {operation} completed.")

    # ---------------------------------------------

    def _show_status_text(self, text):

        canvas = getattr(self.tool_manager, "canvas", None)
        status_bar = getattr(canvas, "status_bar", None)

        if status_bar is not None:
            status_bar.show_status_text(text)

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

    # ---------------------------------------------

    def _show_2d_view(self):

        main_window = getattr(self.tool_manager, "main_window", None)

        if main_window:
            main_window.show_2d_view()

    # ---------------------------------------------

    def _show_3d_view(self):

        main_window = getattr(self.tool_manager, "main_window", None)

        if main_window:
            main_window.show_3d_view()
