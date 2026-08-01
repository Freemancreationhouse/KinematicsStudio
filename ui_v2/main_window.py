from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QDialog, QMainWindow, QVBoxLayout

from engine.cad import CADApplication
from engine.services.project_service import ProjectService
from engine.services.property_command_service import PropertyCommandService
from engine.services.selection_service import SelectionService
from engine.services.workspace_provider import WorkspaceProvider
from engine.tools import (
    AlignedDimensionTool,
    AngularDimensionTool,
    ArcTool,
    ArrayTool,
    BoxPrimitiveTool,
    CapsulePrimitiveTool,
    ChamferTool,
    CircleTool,
    ClosedPolylineTool,
    ConePrimitiveTool,
    CopyTool,
    CubePrimitiveTool,
    CylinderPrimitiveTool,
    DiameterDimensionTool,
    EllipseTool,
    ExplodeBlockTool,
    ExtendTool,
    ExtrudeTool,
    FilletTool,
    HatchTool,
    InsertBlockTool,
    LeaderTool,
    LineTool,
    LinearDimensionTool,
    LoftTool,
    MirrorTool,
    MoveTool,
    MTextTool,
    OffsetTool,
    PlanePrimitiveTool,
    PolygonTool,
    PolylineTool,
    PrismPrimitiveTool,
    PyramidPrimitiveTool,
    RadiusDimensionTool,
    RectangleTool,
    RevolveTool,
    RotateTool,
    ScaleTool,
    SelectTool,
    SmartSketchTool,
    SpherePrimitiveTool,
    SplineTool,
    SweepTool,
    TextTool,
    TorusPrimitiveTool,
    TrimTool,
)
from ui_v2.branding import AboutDialog, BrandAssetLoader, BrandLandingPage
from ui_v2.canvas import Canvas
from ui_v2.command_bar import CommandBar
from ui_v2.command_palette import CommandPalette
from ui_v2.left_toolbox import LeftToolbox
from ui_v2.panel_bootstrap import PanelBootstrap
from ui_v2.property_panel import PropertyPanel
from ui_v2.ribbon import Ribbon
from ui_v2.status_bar import StudioStatusBar
from ui_v2.theme import THEMES
from ui_v2.viewport3d import Viewport3D
from ui_v2.workspace_connection_controller import WorkspaceConnectionController
from ui_v2.workspace_panel_manager import WorkspacePanelManager
from ui_v2.workspace_shell import WorkspaceShell
from ui_v2.viewport_synchronization_service import ViewportSynchronizationService
from ui_v2.workspace_viewport_area import WorkspaceViewportArea


class MainWindow(QMainWindow):
    """Composition root for the Kinematics Studio V2 workspace shell."""

    def __init__(self, brand_loader: BrandAssetLoader | None = None) -> None:
        """Create the application window and compose the approved UI shell."""

        super().__init__()

        self.brand_loader = brand_loader or BrandAssetLoader()

        self.setWindowTitle(self.brand_loader.config.application_name)
        self.setWindowIcon(self.brand_loader.load_icon())

        self.resize(1800, 1000)

        self._create_canvas()
        self._register_tools()
        self._create_permanent_widgets()
        self._create_workspace_shell()
        self.setCentralWidget(self.workspace_shell)
        self._create_panel_manager()
        PanelBootstrap.register_all(
            panel_manager=self.panel_manager,
            app=self.cad_application,
            workspace_provider=self.workspace_provider,
        )
        self._create_command_palette()
        self._create_landing_platform()
        self._create_connection_controller()
        self._create_view_menu()
        self._create_shortcuts()
        self.workspace_connection_controller.connect_all()
        self._restore_window_state()

    def _create_canvas(self) -> None:
        """Create the existing 2D and 3D viewport widgets."""

        self.cad_application = CADApplication()
        self.workspace_provider = WorkspaceProvider(self.cad_application)
        self.project_service = ProjectService(self.cad_application)
        self.selection_service = SelectionService(self.workspace_provider)
        self.property_command_service = PropertyCommandService(
            self.workspace_provider
        )
        self.canvas = Canvas(self.cad_application)
        self.canvas.selection_service = self.selection_service
        self.viewport3d = Viewport3D(self.cad_application)
        self.viewport3d.selection_service = self.selection_service

    def _register_tools(self) -> None:
        """Register all production tools with the existing tool manager."""

        tool_manager = self.cad_application.tool_manager
        tool_manager.register(SelectTool())
        tool_manager.register(LineTool())
        tool_manager.register(RectangleTool())
        tool_manager.register(CircleTool())
        tool_manager.register(ArcTool())
        tool_manager.register(EllipseTool())
        tool_manager.register(PolygonTool())
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
        tool_manager.register(ExtrudeTool())
        tool_manager.register(RevolveTool())
        tool_manager.register(SweepTool())
        tool_manager.register(LoftTool())
        tool_manager.register(SmartSketchTool())
        tool_manager.app = self.cad_application
        tool_manager.project_service = self.project_service
        tool_manager.canvas = self.canvas
        tool_manager.main_window = self

    def _create_permanent_widgets(self) -> None:
        """Create permanent widgets injected into the workspace shell."""

        self.ribbon = Ribbon(self.cad_application)
        self.left_toolbox = LeftToolbox()
        self.viewport_area = WorkspaceViewportArea(
            self.canvas,
            self.viewport3d,
        )
        self.property_panel = PropertyPanel()
        self.command_bar = CommandBar()
        self.command_bar.command.setPlaceholderText(
            "Type a command or press Ctrl+K for the Command Palette..."
        )
        self.studio_status_bar = StudioStatusBar()

    def _create_workspace_shell(self) -> None:
        """Compose the permanent reusable workspace shell."""

        self.workspace_shell = WorkspaceShell(
            self.ribbon,
            self.left_toolbox,
            self.viewport_area,
            self.property_panel,
            self.command_bar,
            self.studio_status_bar,
        )

    def _create_panel_manager(self) -> None:
        """Create the on-demand workspace panel manager."""

        self.panel_manager = WorkspacePanelManager(self)

    def _create_command_palette(self) -> None:
        """Create the command palette without routing it directly."""

        self.command_palette = CommandPalette(self)

    def _create_landing_platform(self) -> None:
        """Create the brand-configured landing platform."""

        self.landing_page = BrandLandingPage(
            self.brand_loader,
            self.cad_application,
            self,
        )
        self.landing_dialog: QDialog | None = None

    def _create_connection_controller(self) -> None:
        """Create the single UI connection controller."""

        self.viewport_synchronization_service = ViewportSynchronizationService(
            workspace_provider=self.workspace_provider,
            viewport_area=self.viewport_area,
        )
        self.workspace_connection_controller = WorkspaceConnectionController(
            ribbon=self.ribbon,
            left_toolbox=self.left_toolbox,
            viewport_area=self.viewport_area,
            property_panel=self.property_panel,
            command_bar=self.command_bar,
            status_bar=self.studio_status_bar,
            command_palette=self.command_palette,
            panel_manager=self.panel_manager,
            project_service=self.project_service,
            property_command_service=self.property_command_service,
            selection_service=self.selection_service,
            viewport_synchronization_service=(
                self.viewport_synchronization_service
            ),
            app=self.cad_application,
            workspace_provider=self.workspace_provider,
            tool_manager=self.cad_application.tool_manager,
            parent=self,
        )

    def _create_view_menu(self) -> None:
        """Create application-level view and panel access menus."""

        view_menu = self.menuBar().addMenu("View")
        self.view_menu = view_menu

        workspace_menu = view_menu.addMenu("Workspace")
        workspace_actions = (
            ("2D View", self.show_2d_view),
            ("3D View", self.show_3d_view),
            ("Home View", lambda: self.workspace_connection_controller.route_action("view:home")),
            ("Zoom Extents", lambda: self.workspace_connection_controller.route_action("view:zoom_extents")),
            ("Zoom Selected", lambda: self.workspace_connection_controller.route_action("view:zoom_selected")),
            ("Command Palette", self.show_command_palette),
            ("Focus Mode", self.enter_focus_mode),
            ("Presentation Mode", self.enter_presentation_mode),
            ("Reset Workspace Layout", self.reset_workspace_layout),
        )
        for title, callback in workspace_actions:
            action = QAction(title, self)
            action.triggered.connect(callback)
            workspace_menu.addAction(action)

        view_menu.addSeparator()
        panels_menu = view_menu.addMenu("Panels")
        for definition in self.panel_manager.registry.definitions():
            action = QAction(definition.title, self)
            action.triggered.connect(
                lambda checked=False, panel_id=definition.id: (
                    self.workspace_connection_controller.route_action(
                        f"panel:{panel_id}"
                    )
                )
            )
            panels_menu.addAction(action)

    def _create_shortcuts(self) -> None:
        """Create application-level shortcuts routed through wrappers."""

        self.command_palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.command_palette_shortcut.activated.connect(self.show_command_palette)
        self.delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        self.delete_shortcut.activated.connect(
            lambda: self.workspace_connection_controller.route_action(
                "command:delete"
            )
        )

    def show_2d_view(self) -> None:
        """Compatibility wrapper for switching to the 2D viewport."""

        self.workspace_connection_controller.route_action("view_2d")

    def show_3d_view(self) -> None:
        """Compatibility wrapper for switching to the 3D viewport."""

        self.workspace_connection_controller.route_action("view_3d")

    def show_command_palette(self) -> None:
        """Compatibility wrapper for opening the command palette."""

        self.workspace_connection_controller.route_action("command_palette")

    def enter_focus_mode(self) -> None:
        """Compatibility wrapper for requesting focus mode."""

        self.workspace_connection_controller.route_action("focus_mode")

    def enter_presentation_mode(self) -> None:
        """Compatibility wrapper for requesting presentation mode."""

        self.workspace_connection_controller.route_action("presentation_mode")

    def reset_workspace_layout(self) -> None:
        """Compatibility wrapper for restoring the permanent shell layout."""

        self.workspace_connection_controller.route_action("reset_workspace_layout")

    def show_landing_experience(self) -> None:
        """Open the brand-configured landing experience."""

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{self.brand_loader.config.application_name} Landing")
        dialog.setWindowIcon(self.brand_loader.load_icon())
        layout = QVBoxLayout(dialog)
        layout.addWidget(
            BrandLandingPage(self.brand_loader, self.cad_application, dialog)
        )
        dialog.resize(960, 640)
        self.landing_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_about_dialog(self) -> None:
        """Open the application-shell about dialog from external brand config."""

        dialog = AboutDialog(self.brand_loader, self)
        dialog.exec()

    def apply_theme(self, name: str) -> None:
        """Apply a certified application theme."""

        stylesheet = THEMES.get(name, THEMES["Dark"])
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet(stylesheet)
        self.current_theme = name

    def closeEvent(self, event: QCloseEvent) -> None:
        """Persist geometry and close transient panel windows before shutdown."""

        self._save_window_state()
        self.panel_manager.lifecycle.close_all()
        self.workspace_connection_controller.disconnect_all()
        super().closeEvent(event)

    def _restore_window_state(self) -> None:
        """Restore saved top-level window geometry when available."""

        settings = QSettings(
            self.brand_loader.config.company,
            self.brand_loader.config.application_name,
        )
        geometry = settings.value("main_window/geometry")

        if geometry:
            self.restoreGeometry(geometry)

    def _save_window_state(self) -> None:
        """Save top-level window geometry for the next launch."""

        settings = QSettings(
            self.brand_loader.config.company,
            self.brand_loader.config.application_name,
        )
        settings.setValue("main_window/geometry", self.saveGeometry())
