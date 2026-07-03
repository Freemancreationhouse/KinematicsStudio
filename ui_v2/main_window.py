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
        self.explorer_dock.setWidget(ExplorerPanel())

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.explorer_dock
        )

        # ---------------------------------
        # Property Dock
        # ---------------------------------

        self.property_dock = QDockWidget("Properties", self)
        self.property_dock.setWidget(PropertyPanel())

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.property_dock
        )

        # ---------------------------------
        # Status Bar
        # ---------------------------------

        self.setStatusBar(
            StudioStatusBar()
        )