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
from ui_v2.layer_manager_panel import LayerManagerPanel
from ui_v2.block_manager_panel import BlockManagerPanel
from ui_v2.command_bar import CommandBar
from ui_v2.status_bar import StudioStatusBar

from engine.tools import (
    SelectTool,
    LineTool,
    RectangleTool,
    CircleTool,
    MoveTool,
    TrimTool,
    ExtendTool,
    OffsetTool,
    RotateTool,
    MirrorTool,
    ScaleTool,
    CopyTool,
    ArrayTool,
    FilletTool,
    ChamferTool,
    SmartSketchTool,
)


class MainWindow(QMainWindow):
    """Main application window for the V2 workspace."""

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Kinematics Studio V2")

        self.resize(1800, 1000)

        self._create_canvas()
        self._create_central_layout()
        self._create_docks()
        self._create_status_bar()
        self._wire_ui()

    # ---------------------------------

    def _create_canvas(self):

        self.canvas = Canvas()
        self._register_tools(self.canvas.app.tool_manager)

    # ---------------------------------

    def _register_tools(self, tool_manager):

        tool_manager.register(SelectTool())
        tool_manager.register(LineTool())
        tool_manager.register(RectangleTool())
        tool_manager.register(CircleTool())
        tool_manager.register(MoveTool())
        tool_manager.register(TrimTool())
        tool_manager.register(ExtendTool())
        tool_manager.register(OffsetTool())
        tool_manager.register(RotateTool())
        tool_manager.register(MirrorTool())
        tool_manager.register(ScaleTool())
        tool_manager.register(CopyTool())
        tool_manager.register(ArrayTool())
        tool_manager.register(FilletTool())
        tool_manager.register(ChamferTool())
        tool_manager.register(SmartSketchTool())

    # ---------------------------------

    def _create_central_layout(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.ribbon = Ribbon(self.canvas.app.tool_manager)
        layout.addWidget(self.ribbon)

        layout.addWidget(self.canvas, 1)

        self.command_bar = CommandBar()
        layout.addWidget(self.command_bar)

    # ---------------------------------

    def _create_docks(self):

        self.explorer_dock = QDockWidget("Explorer", self)
        self.explorer_panel = ExplorerPanel()
        self.explorer_dock.setWidget(self.explorer_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.explorer_dock)

        self.property_dock = QDockWidget("Properties", self)
        self.property_panel = PropertyPanel()
        self.property_dock.setWidget(self.property_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_dock)

        self.layer_dock = QDockWidget("Layer Manager", self)
        self.layer_panel = LayerManagerPanel(
            self.canvas.app.workspace,
            self._layers_changed
        )
        self.layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_dock)

        self.block_dock = QDockWidget("Block Manager", self)
        self.block_panel = BlockManagerPanel(
            self.canvas.app.workspace,
            self._blocks_changed
        )
        self.block_dock.setWidget(self.block_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.block_dock)

    # ---------------------------------

    def _create_status_bar(self):

        self.studio_status_bar = StudioStatusBar()
        self.setStatusBar(self.studio_status_bar)

    # ---------------------------------

    def _wire_ui(self):

        tm = self.canvas.app.tool_manager

        self.canvas.property_panel = self.property_panel
        self.canvas.status_bar = self.studio_status_bar
        self.property_panel.set_workspace(
            self.canvas.app.workspace,
            self._property_changed
        )

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
        self.layer_panel.refresh()
        self.block_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()

    # ---------------------------------

    def _layers_changed(self):

        self.canvas._sync_selection_ui()
        self.canvas.update()

    # ---------------------------------

    def _property_changed(self):

        self.layer_panel.refresh()
        self.block_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()

    # ---------------------------------

    def _blocks_changed(self):

        self.block_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
