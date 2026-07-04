from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QDockWidget,
)

from ui_v2.canvas import Canvas
from ui_v2.ribbon import Ribbon
from ui_v2.explorer_panel import ExplorerPanel
from ui_v2.property_panel import PropertyPanel
from ui_v2.command_bar import CommandBar
from ui_v2.status_bar import StudioStatusBar

from engine.tools import (
    SelectTool,
    LineTool,
    RectangleTool,
    CircleTool,
    MoveTool,
    SmartSketchTool,
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Kinematics Studio V2")

        self.resize(1800, 1000)

        # ---------------------------------
        # Canvas
        # ---------------------------------

        self.canvas = Canvas()

        tm = self.canvas.app.tool_manager

        tm.register(SelectTool())
        tm.register(LineTool())
        tm.register(RectangleTool())
        tm.register(CircleTool())
        tm.register(MoveTool())
        tm.register(SmartSketchTool())

        # ---------------------------------
        # Central Widget
        # ---------------------------------

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        layout.setContentsMargins(0, 0, 0, 0)

        # Ribbon
        self.ribbon = Ribbon(tm)
        layout.addWidget(self.ribbon)

        # Canvas
        layout.addWidget(self.canvas, 1)

        # Command Bar
        self.command_bar = CommandBar()
        layout.addWidget(self.command_bar)

        # ---------------------------------
        # Explorer Dock
        # ---------------------------------

        self.explorer_dock = QDockWidget("Explorer", self)
        self.explorer_panel = ExplorerPanel()
        self.explorer_dock.setWidget(self.explorer_panel)

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.explorer_dock
        )

        # ---------------------------------
        # Property Dock
        # ---------------------------------

        self.property_dock = QDockWidget("Properties", self)
        self.property_panel = PropertyPanel()
        self.property_dock.setWidget(self.property_panel)

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.property_dock
        )

        # ---------------------------------
        # Status Bar
        # ---------------------------------

        self.studio_status_bar = StudioStatusBar()
        self.setStatusBar(self.studio_status_bar)

        self.canvas.property_panel = self.property_panel
        self.canvas.status_bar = self.studio_status_bar

        tm.on_change = self._tool_changed
        tm.app = self.canvas.app
        tm.canvas = self.canvas
        self.canvas.app.workspace.command_manager.on_change = self._commands_changed
        self._commands_changed(self.canvas.app.workspace.command_manager)

    # ---------------------------------

    def _tool_changed(self, tool):

        self.studio_status_bar.show_tool(tool)
        self.canvas._sync_selection_ui()

    # ---------------------------------

    def _commands_changed(self, command_manager):

        self.explorer_panel.show_history(command_manager)
        self.studio_status_bar.show_command_state(command_manager)
        self.canvas._sync_selection_ui()
        self.canvas.update()
