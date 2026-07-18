from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QDockWidget,
    QStackedWidget,
)

from ui_v2.canvas import Canvas
from ui_v2.viewport3d import Viewport3D
from ui_v2.ribbon import Ribbon
from ui_v2.explorer_panel import ExplorerPanel
from ui_v2.property_panel import PropertyPanel
from ui_v2.layer_manager_panel import LayerManagerPanel
from ui_v2.dimension_manager_panel import DimensionManagerPanel
from ui_v2.pattern_manager_panel import PatternManagerPanel
from ui_v2.block_manager_panel import BlockManagerPanel
from ui_v2.group_manager_panel import GroupManagerPanel
from ui_v2.selection_set_manager_panel import SelectionSetManagerPanel
from ui_v2.constraint_manager_panel import ConstraintManagerPanel
from ui_v2.project_manager_panel import ProjectManagerPanel
from ui_v2.reference_browser_panel import ReferenceBrowserPanel
from ui_v2.reference_layer_panel import ReferenceLayerPanel
from ui_v2.coordination_panel import CoordinationPanel
from ui_v2.clash_manager_panel import ClashManagerPanel
from ui_v2.clash_dashboard_panel import ClashDashboardPanel
from ui_v2.bcf_topic_browser_panel import BCFTopicBrowserPanel
from ui_v2.command_bar import CommandBar
from ui_v2.status_bar import StudioStatusBar

from engine.tools import (
    SelectTool,
    LineTool,
    RectangleTool,
    CircleTool,
    PolylineTool,
    ClosedPolylineTool,
    SplineTool,
    TextTool,
    MTextTool,
    LeaderTool,
    HatchTool,
    LinearDimensionTool,
    AlignedDimensionTool,
    RadiusDimensionTool,
    DiameterDimensionTool,
    AngularDimensionTool,
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
    InsertBlockTool,
    ExplodeBlockTool,
    BoxPrimitiveTool,
    CapsulePrimitiveTool,
    ConePrimitiveTool,
    CubePrimitiveTool,
    CylinderPrimitiveTool,
    PlanePrimitiveTool,
    PrismPrimitiveTool,
    PyramidPrimitiveTool,
    SpherePrimitiveTool,
    TorusPrimitiveTool,
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
        self._restore_window_state()

    # ---------------------------------

    def _create_canvas(self):

        self.canvas = Canvas()
        self.viewport3d = Viewport3D(self.canvas.app)
        self._register_tools(self.canvas.app.tool_manager)

    # ---------------------------------

    def _register_tools(self, tool_manager):

        tool_manager.register(SelectTool())
        tool_manager.register(LineTool())
        tool_manager.register(RectangleTool())
        tool_manager.register(CircleTool())
        tool_manager.register(PolylineTool())
        tool_manager.register(ClosedPolylineTool())
        tool_manager.register(SplineTool())
        tool_manager.register(TextTool())
        tool_manager.register(MTextTool())
        tool_manager.register(LeaderTool())
        tool_manager.register(HatchTool())
        tool_manager.register(LinearDimensionTool())
        tool_manager.register(AlignedDimensionTool())
        tool_manager.register(RadiusDimensionTool())
        tool_manager.register(DiameterDimensionTool())
        tool_manager.register(AngularDimensionTool())
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
        tool_manager.register(InsertBlockTool())
        tool_manager.register(ExplodeBlockTool())
        tool_manager.register(CubePrimitiveTool())
        tool_manager.register(BoxPrimitiveTool())
        tool_manager.register(PlanePrimitiveTool())
        tool_manager.register(CylinderPrimitiveTool())
        tool_manager.register(ConePrimitiveTool())
        tool_manager.register(SpherePrimitiveTool())
        tool_manager.register(TorusPrimitiveTool())
        tool_manager.register(PyramidPrimitiveTool())
        tool_manager.register(PrismPrimitiveTool())
        tool_manager.register(CapsulePrimitiveTool())
        tool_manager.register(SmartSketchTool())

    # ---------------------------------

    def _create_central_layout(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.ribbon = Ribbon(self.canvas.app.tool_manager)
        layout.addWidget(self.ribbon)

        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.canvas)
        self.view_stack.addWidget(self.viewport3d)
        layout.addWidget(self.view_stack, 1)

        self.command_bar = CommandBar()
        layout.addWidget(self.command_bar)

    # ---------------------------------

    def _create_docks(self):
        self.setDockOptions(
            QMainWindow.AllowNestedDocks
            | QMainWindow.AllowTabbedDocks
            | QMainWindow.AnimatedDocks
        )

        self.explorer_dock = QDockWidget("Explorer", self)
        self.explorer_dock.setObjectName("ExplorerDock")
        self.explorer_dock.setToolTip("Project browser and drawing history.")
        self.explorer_panel = ExplorerPanel()
        self.explorer_dock.setWidget(self.explorer_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.explorer_dock)

        self.property_dock = QDockWidget("Properties", self)
        self.property_dock.setObjectName("PropertiesDock")
        self.property_dock.setToolTip("Selected entity properties and edits.")
        self.property_panel = PropertyPanel()
        self.property_dock.setWidget(self.property_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_dock)

        self.layer_dock = QDockWidget("Layer Manager", self)
        self.layer_dock.setObjectName("LayerManagerDock")
        self.layer_dock.setToolTip("Layer visibility, locking, and appearance.")
        self.layer_panel = LayerManagerPanel(
            self.canvas.app.workspace,
            self._layers_changed
        )
        self.layer_dock.setWidget(self.layer_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_dock)

        self.dimension_dock = QDockWidget("Dimension Manager", self)
        self.dimension_dock.setObjectName("DimensionManagerDock")
        self.dimension_dock.setToolTip("Dimension style management.")
        self.dimension_panel = DimensionManagerPanel(
            self.canvas.app.workspace,
            self._dimensions_changed
        )
        self.dimension_dock.setWidget(self.dimension_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dimension_dock)

        self.pattern_dock = QDockWidget("Pattern Manager", self)
        self.pattern_dock.setObjectName("PatternManagerDock")
        self.pattern_dock.setToolTip("Hatch pattern management.")
        self.pattern_panel = PatternManagerPanel(
            self.canvas.app.workspace,
            self._patterns_changed
        )
        self.pattern_dock.setWidget(self.pattern_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.pattern_dock)

        self.block_dock = QDockWidget("Block Manager", self)
        self.block_dock.setObjectName("BlockManagerDock")
        self.block_dock.setToolTip("Block definition management.")
        self.block_panel = BlockManagerPanel(
            self.canvas.app.workspace,
            self._blocks_changed
        )
        self.block_dock.setWidget(self.block_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.block_dock)

        self.group_dock = QDockWidget("Group Manager", self)
        self.group_dock.setObjectName("GroupManagerDock")
        self.group_dock.setToolTip("Group membership and organization.")
        self.group_panel = GroupManagerPanel(
            self.canvas.app.workspace,
            self._groups_changed
        )
        self.group_dock.setWidget(self.group_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.group_dock)

        self.selection_set_dock = QDockWidget("Selection Sets", self)
        self.selection_set_dock.setObjectName("SelectionSetsDock")
        self.selection_set_dock.setToolTip("Named selection set management.")
        self.selection_set_panel = SelectionSetManagerPanel(
            self.canvas.app.workspace,
            self._selection_sets_changed
        )
        self.selection_set_dock.setWidget(self.selection_set_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.selection_set_dock)

        self.constraint_dock = QDockWidget("Constraint Manager", self)
        self.constraint_dock.setObjectName("ConstraintManagerDock")
        self.constraint_dock.setToolTip("Geometric and dimensional constraints.")
        self.constraint_panel = ConstraintManagerPanel(
            self.canvas.app.workspace,
            self._constraints_changed
        )
        self.constraint_dock.setWidget(self.constraint_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.constraint_dock)

        self.project_dock = QDockWidget("Project Manager", self)
        self.project_dock.setObjectName("ProjectManagerDock")
        self.project_dock.setToolTip("Project path, save, autosave, and counts.")
        self.project_panel = ProjectManagerPanel(self.canvas.app)
        self.project_dock.setWidget(self.project_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_dock)

        self.reference_dock = QDockWidget("Reference Browser", self)
        self.reference_dock.setObjectName("ReferenceBrowserDock")
        self.reference_dock.setToolTip("Imported 3D references and external links.")
        self.reference_panel = ReferenceBrowserPanel(
            self.canvas.app.workspace,
            self._references_changed
        )
        self.reference_dock.setWidget(self.reference_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.reference_dock)

        self.reference_layer_dock = QDockWidget("Reference Layers", self)
        self.reference_layer_dock.setObjectName("ReferenceLayerDock")
        self.reference_layer_dock.setToolTip("Reference layer mapping, visibility, locking, and styling.")
        self.reference_layer_panel = ReferenceLayerPanel(
            self.canvas.app.workspace,
            self._references_changed
        )
        self.reference_layer_dock.setWidget(self.reference_layer_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.reference_layer_dock)

        self.coordination_dock = QDockWidget("Coordination", self)
        self.coordination_dock.setObjectName("CoordinationDock")
        self.coordination_dock.setToolTip("Reference alignment, offsets, rotation, scale, and validation.")
        self.coordination_panel = CoordinationPanel(
            self.canvas.app.workspace,
            self._references_changed
        )
        self.coordination_dock.setWidget(self.coordination_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.coordination_dock)

        self.clash_dock = QDockWidget("Clash Manager", self)
        self.clash_dock.setObjectName("ClashManagerDock")
        self.clash_dock.setToolTip("Clash review, navigation, grouping, and reports.")
        self.clash_panel = ClashManagerPanel(
            self.canvas.app.workspace,
            self._clashes_changed
        )
        self.clash_dock.setWidget(self.clash_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.clash_dock)

        self.clash_dashboard_dock = QDockWidget("Clash Dashboard", self)
        self.clash_dashboard_dock.setObjectName("ClashDashboardDock")
        self.clash_dashboard_dock.setToolTip("Clash statistics, assignments, templates, and dashboard filters.")
        self.clash_dashboard_panel = ClashDashboardPanel(
            self.canvas.app.workspace,
            self._clashes_changed
        )
        self.clash_dashboard_dock.setWidget(self.clash_dashboard_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.clash_dashboard_dock)

        self.bcf_dock = QDockWidget("BCF Topics", self)
        self.bcf_dock.setObjectName("BCFTopicBrowserDock")
        self.bcf_dock.setToolTip("BCF coordination projects, topics, comments, viewpoints, and selection sync.")
        self.bcf_panel = BCFTopicBrowserPanel(
            self.canvas.app.workspace,
            self._bcf_changed
        )
        self.bcf_dock.setWidget(self.bcf_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.bcf_dock)

    # ---------------------------------

    def _create_status_bar(self):

        self.studio_status_bar = StudioStatusBar()
        self.setStatusBar(self.studio_status_bar)

    # ---------------------------------

    def _wire_ui(self):

        tm = self.canvas.app.tool_manager

        self.canvas.property_panel = self.property_panel
        self.canvas.status_bar = self.studio_status_bar
        self.viewport3d.property_panel = self.property_panel
        self.viewport3d.status_bar = self.studio_status_bar
        self.canvas.on_project_loaded = self._project_loaded
        self.canvas.on_project_state_changed = self._project_state_changed
        self.property_panel.set_workspace(
            self.canvas.app.workspace,
            self._property_changed
        )

        tm.on_change = self._tool_changed
        tm.app = self.canvas.app
        tm.canvas = self.canvas
        tm.main_window = self
        self.canvas.app.workspace.command_manager.on_change = self._commands_changed
        self._commands_changed(self.canvas.app.workspace.command_manager)

    # ---------------------------------

    def _project_loaded(self):

        workspace = self.canvas.app.workspace
        self.property_panel.set_workspace(workspace, self._property_changed)
        self.layer_panel.workspace = workspace
        self.dimension_panel.workspace = workspace
        self.pattern_panel.workspace = workspace
        self.block_panel.workspace = workspace
        self.group_panel.workspace = workspace
        self.selection_set_panel.workspace = workspace
        self.constraint_panel.workspace = workspace
        self.reference_panel.workspace = workspace
        self.reference_layer_panel.workspace = workspace
        self.coordination_panel.workspace = workspace
        self.clash_panel.workspace = workspace
        self.clash_dashboard_panel.workspace = workspace
        self.bcf_panel.workspace = workspace
        workspace.command_manager.on_change = self._commands_changed
        self._commands_changed(workspace.command_manager)
        self._project_state_changed()

    # ---------------------------------

    def _project_state_changed(self):

        self.project_panel.refresh()

    # ---------------------------------

    def _tool_changed(self, tool):

        self.studio_status_bar.show_tool(tool)
        self.canvas._sync_selection_ui()

    # ---------------------------------

    def _commands_changed(self, command_manager):

        self.explorer_panel.show_history(command_manager)
        self.studio_status_bar.show_command_state(command_manager)
        self.layer_panel.refresh()
        self.dimension_panel.refresh()
        self.pattern_panel.refresh()
        self.block_panel.refresh()
        self.group_panel.refresh()
        self.selection_set_panel.refresh()
        self.constraint_panel.refresh()
        self.reference_panel.refresh()
        self.reference_layer_panel.refresh()
        self.coordination_panel.refresh()
        self.clash_panel.refresh()
        self.clash_dashboard_panel.refresh()
        self.bcf_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _layers_changed(self):

        self.canvas._sync_selection_ui()
        self.selection_set_panel.refresh()
        self.project_panel.refresh()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _property_changed(self):

        self.layer_panel.refresh()
        self.dimension_panel.refresh()
        self.pattern_panel.refresh()
        self.block_panel.refresh()
        self.group_panel.refresh()
        self.selection_set_panel.refresh()
        self.constraint_panel.refresh()
        self.reference_panel.refresh()
        self.reference_layer_panel.refresh()
        self.coordination_panel.refresh()
        self.clash_panel.refresh()
        self.clash_dashboard_panel.refresh()
        self.bcf_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _blocks_changed(self):

        self.block_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _dimensions_changed(self):

        self.dimension_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _patterns_changed(self):

        self.pattern_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _groups_changed(self):

        self.group_panel.refresh()
        self.selection_set_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _selection_sets_changed(self):

        self.selection_set_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _constraints_changed(self):

        self.constraint_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _references_changed(self):

        self.reference_panel.refresh()
        self.reference_layer_panel.refresh()
        self.coordination_panel.refresh()
        self.clash_panel.refresh()
        self.clash_dashboard_panel.refresh()
        self.bcf_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _clashes_changed(self):

        self.clash_panel.refresh()
        self.clash_dashboard_panel.refresh()
        self.bcf_panel.refresh()
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def _bcf_changed(self):

        self.bcf_panel.refresh()
        self.clash_panel.refresh()
        self.clash_dashboard_panel.refresh()
        self.property_panel.show_selection(self.canvas.app.workspace.selection.selected)
        self.project_panel.refresh()
        self.canvas._sync_selection_ui()
        self.canvas.update()
        self.viewport3d.update()

    # ---------------------------------

    def show_2d_view(self):
        """Switch to the existing 2D canvas without changing 2D workflows."""

        self.view_stack.setCurrentWidget(self.canvas)
        self.canvas.setFocus()
        self.canvas.update()
        self.studio_status_bar.tool.setText("Tool: 2D View")

    # ---------------------------------

    def show_3d_view(self):
        """Switch to the 3D foundation viewport."""

        self.view_stack.setCurrentWidget(self.viewport3d)
        self.viewport3d.setFocus()
        self.viewport3d._show_status()
        self.viewport3d.update()

    # ---------------------------------

    def closeEvent(self, event):
        """Persist window and dock layout before shutdown."""

        self._save_window_state()
        super().closeEvent(event)

    # ---------------------------------

    def _restore_window_state(self):
        """Restore saved dock placement when available."""

        settings = QSettings("Kinematics Studio", "Kinematics Studio V2")
        geometry = settings.value("main_window/geometry")
        state = settings.value("main_window/state")

        if geometry:
            self.restoreGeometry(geometry)

        if state:
            self.restoreState(state)

    # ---------------------------------

    def _save_window_state(self):
        """Save dock placement and window geometry for the next launch."""

        settings = QSettings("Kinematics Studio", "Kinematics Studio V2")
        settings.setValue("main_window/geometry", self.saveGeometry())
        settings.setValue("main_window/state", self.saveState())
