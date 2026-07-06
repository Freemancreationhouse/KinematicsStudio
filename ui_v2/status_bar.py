from PySide6.QtWidgets import (
    QStatusBar,
    QLabel,
)


class StudioStatusBar(QStatusBar):
    """Displays view, tool, selection, snap, command, and machine status."""

    def __init__(self):

        super().__init__()

        self.coords = QLabel("X:0  Y:0")
        self.view = QLabel("Zoom: 100%  Camera: 0,0")

        self.snap = QLabel("Snap : OFF")

        self.tool = QLabel("Tool: Select")

        self.selected = QLabel("Selected: None")

        self.undo = QLabel("Undo Available: No")

        self.redo = QLabel("Redo Available: No")

        self.machine = QLabel("Machine: Disconnected")

        self.addPermanentWidget(self.coords)
        self.addPermanentWidget(self.view)

        self.addPermanentWidget(self.snap)

        self.addPermanentWidget(self.tool)

        self.addPermanentWidget(self.selected)

        self.addPermanentWidget(self.undo)

        self.addPermanentWidget(self.redo)

        self.addPermanentWidget(self.machine)

    # -----------------------------------------

    def show_selection(self, selected):

        if not selected:
            self.selected.setText("Selected: None")
        elif len(selected) == 1:
            self.selected.setText(f"Selected: {selected[0].type_name}")
        else:
            self.selected.setText(f"Selected: Multiple ({len(selected)})")

    # -----------------------------------------

    def show_selection_count(self, selected):

        self.selected.setText(f"Selected: {len(selected)}")

    # -----------------------------------------

    def show_status_text(self, text):

        self.selected.setText(text)

    # -----------------------------------------

    def show_tool(self, tool):

        name = getattr(tool, "name", "SelectTool")

        if name.endswith("Tool"):
            name = name[:-4]

        self.tool.setText(f"Tool: {name}")

    # -----------------------------------------

    def show_command_state(self, command_manager):

        undo = "Yes" if command_manager.undo_available else "No"
        redo = "Yes" if command_manager.redo_available else "No"

        self.undo.setText(f"Undo Available: {undo}")
        self.redo.setText(f"Redo Available: {redo}")

    # -----------------------------------------

    def show_coordinates(self, point, camera):

        self.coords.setText(f"X:{point.x:.2f}  Y:{point.y:.2f}")
        self.view.setText(
            f"Zoom: {camera.zoom * 100:.0f}%  "
            f"Camera: {camera.position.x:.2f},{camera.position.y:.2f}"
        )

    # -----------------------------------------

    def show_snap(self, mode):

        self.snap.setText(f"Snap : {mode}")
