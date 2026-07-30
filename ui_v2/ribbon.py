from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from engine.commands import (
    CancelAITaskCommand,
    CancelManufacturingJobCommand,
    CaptureAIDiagnosticsCommand,
    CaptureAIContextCommand,
    CaptureMachineDiagnosticsCommand,
    CreateAISessionCommand,
    CreateMachineProfileCommand,
    CreateManufacturingJobCommand,
    ExecuteManufacturingJobCommand,
    ExportManufacturingJobCommand,
    GenerateToolpathCommand,
    PauseManufacturingJobCommand,
    PostProcessManufacturingJobCommand,
    QueueManufacturingJobCommand,
    ResumeManufacturingJobCommand,
    RetryAIPromptCommand,
    SaveExchangeProfileCommand,
    SimulateManufacturingJobCommand,
    StoreExchangeValidationReportCommand,
    SubmitAIPromptCommand,
    UpdateExchangeSettingsCommand,
    ValidateAIProvidersCommand,
    ValidateAIPromptCommand,
)
from engine.commands.occ_boolean_command import OCCBooleanCommand
from engine.commands.occ_import_command import ImportOCCShapeCommand
from engine.storage import ProjectTemplateManager
from ui_v2.exchange_dialogs import (
    ExchangeExportDialog,
    ExchangeImportDialog,
    ExchangeValidationReportPanel,
)
from ui_v2.import_options_dialog import ImportOptionsDialog


@dataclass(frozen=True)
class RibbonCommand:
    """Definition for a command displayed in a ribbon group."""

    text: str
    icon: str
    tooltip: str
    callback: Callable[[], None]
    large: bool = False


class RibbonButton(QPushButton):
    """Compact CAD-style ribbon button with generated icon and text."""

    def __init__(self, command: RibbonCommand, parent: QWidget | None = None) -> None:
        """Create a themed ribbon command button."""

        super().__init__(command.text, parent)

        self.setObjectName("RibbonButtonLarge" if command.large else "RibbonButton")
        self.setToolTip(command.tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(self._icon(command.icon, command.large))
        self.setIconSize(QSize(28, 28) if command.large else QSize(18, 18))
        self.setMinimumHeight(64 if command.large else 28)
        self.setMinimumWidth(72 if command.large else 92)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clicked.connect(lambda checked=False: command.callback())

    def _icon(self, glyph: str, large: bool) -> QIcon:
        """Create a crisp generated icon for a ribbon command."""

        size = 32 if large else 22
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#d7dde7"), 1.6))
        font = painter.font()
        font.setPixelSize(18 if large else 13)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, glyph)
        painter.end()

        return QIcon(pixmap)


class RibbonGroup(QFrame):
    """Reusable titled ribbon group with large and small command placement."""

    def __init__(
        self,
        title: str,
        commands: tuple[RibbonCommand, ...],
        parent: QWidget | None = None,
    ) -> None:
        """Create a professional ribbon group."""

        super().__init__(parent)

        self.setObjectName("RibbonGroup")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 5, 6, 3)
        root.setSpacing(3)

        command_layout = QGridLayout()
        command_layout.setContentsMargins(0, 0, 0, 0)
        command_layout.setHorizontalSpacing(4)
        command_layout.setVerticalSpacing(3)
        root.addLayout(command_layout, 1)

        large_column = 0
        small_column = 0
        small_row = 0

        for command in commands:
            button = RibbonButton(command, self)
            if command.large:
                command_layout.addWidget(button, 0, large_column, 3, 1)
                large_column += 1
                small_column = max(small_column, large_column)
            else:
                command_layout.addWidget(button, small_row, small_column)
                small_row += 1
                if small_row >= 3:
                    small_row = 0
                    small_column += 1

        title_label = QLabel(title, self)
        title_label.setObjectName("RibbonGroupTitle")
        title_label.setAlignment(Qt.AlignCenter)
        root.addWidget(title_label)


class RibbonPage(QWidget):
    """Scrollable ribbon page containing titled command groups."""

    def __init__(
        self,
        groups: tuple[tuple[str, tuple[RibbonCommand, ...]], ...],
        parent: QWidget | None = None,
    ) -> None:
        """Create a ribbon page from grouped commands."""

        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        for title, commands in groups:
            layout.addWidget(RibbonGroup(title, commands, self))

        layout.addStretch(1)


class Ribbon(QWidget):
    """Compact professional CAD ribbon for Kinematics Studio."""

    HIDDEN_TABS: set[str] = set()

    def __init__(self, app) -> None:
        """Create the ribbon using the injected CAD application runtime."""

        super().__init__()

        self.app = app
        self.tool_manager = getattr(app, "tool_manager", app)
        self.setObjectName("Ribbon")
        self.setMaximumHeight(120)
        self.setMinimumHeight(104)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("RibbonTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        layout.addWidget(self.tabs)

        self._build_tabs()
        self._apply_style()

    def _build_tabs(self) -> None:
        """Build all production ribbon tabs."""

        self._add_tab("Project", self._project_groups())
        self._add_tab("Draw", self._draw_groups())
        self._add_tab("Modify", self._modify_groups())
        self._add_tab("3D", self._three_d_groups())
        self._add_tab("BIM", self._bim_groups())
        self._add_tab("Analyze", self._analyze_groups())
        self._add_tab("Fabrication", self._fabrication_groups())
        self._add_tab("AI", self._ai_groups())
        self._add_tab("View", self._view_groups())
        self._add_tab("Manage", self._manage_groups())

    def _add_tab(
        self,
        title: str,
        groups: tuple[tuple[str, tuple[RibbonCommand, ...]], ...],
    ) -> None:
        """Add a scrollable tab page."""

        if title in self.HIDDEN_TABS:
            return

        scroll = QScrollArea(self.tabs)
        scroll.setObjectName("RibbonScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(RibbonPage(groups, scroll))
        self.tabs.addTab(scroll, title)

    def _project_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return project ribbon groups."""

        return (
            (
                "Project",
                (
                    self._command("New", "N", "Create a blank project.", self._new_blank, True),
                    self._command("Open", "O", "Open an existing project.", self._open),
                    self._command("Save", "S", "Save the current project.", self._save),
                    self._command("Save As", "⇧S", "Save the project to a new file.", self._save_as),
                ),
            ),
            (
                "Templates",
                (
                    self._command("Architectural", "A", "Create from architectural template.", self._new_architectural),
                    self._command("Mechanical", "M", "Create from mechanical template.", self._new_mechanical),
                    self._command("Recover", "R", "Recover the latest autosave.", self._recover),
                    self._command("Auto Save", "⟳", "Toggle autosave.", self._toggle_autosave),
                ),
            ),
            (
                "Import / Export",
                (
                    self._command("Import 3D", "I", "Import an external 3D reference.", self._import_3d, True),
                    self._command("Import CAD", "⇩", "Import professional CAD exchange data.", self._import_cad_exchange),
                    self._command("Export CAD", "⇧", "Export professional CAD exchange data.", self._export_cad_exchange),
                    self._command("Validate", "✓", "Show exchange validation report.", self._show_validation_report),
                    self._command("DXF", "D", "Export DXF drawing.", lambda: self._export("dxf", "DXF Drawing (*.dxf)")),
                    self._command("SVG", "V", "Export SVG drawing.", lambda: self._export("svg", "SVG Drawing (*.svg)")),
                    self._command("PDF", "P", "Export PDF drawing.", lambda: self._export("pdf", "PDF Drawing (*.pdf)")),
                    self._command("PNG", "G", "Export PNG image.", lambda: self._export("png", "PNG Image (*.png)")),
                ),
            ),
        )

    def _draw_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return drawing ribbon groups."""

        return (
            (
                "Basic Geometry",
                (
                    self._tool("Line", "L", "LineTool", True),
                    self._tool("Polyline", "PL", "PolylineTool"),
                    self._tool("Rectangle", "▭", "RectangleTool", True),
                    self._tool("Circle", "○", "CircleTool", True),
                ),
            ),
            (
                "Curves",
                (
                    self._tool("Arc", "⌒", "ArcTool"),
                    self._tool("Ellipse", "⬭", "EllipseTool"),
                    self._tool("Spline", "∿", "SplineTool"),
                    self._tool("Polygon", "⬡", "PolygonTool"),
                    self._tool("Closed Poly", "◆", "ClosedPolylineTool"),
                ),
            ),
            (
                "Annotation",
                (
                    self._tool("Text", "T", "TextTool"),
                    self._tool("MText", "MT", "MTextTool"),
                    self._tool("Leader", "↗", "LeaderTool"),
                    self._tool("Hatch", "▧", "HatchTool"),
                ),
            ),
            (
                "Dimensions",
                (
                    self._tool("Linear", "↔", "LinearDimensionTool"),
                    self._tool("Aligned", "⟋", "AlignedDimensionTool"),
                    self._tool("Radius", "R", "RadiusDimensionTool"),
                    self._tool("Diameter", "Ø", "DiameterDimensionTool"),
                    self._tool("Angular", "∠", "AngularDimensionTool"),
                ),
            ),
        )

    def _modify_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return modify ribbon groups."""

        return (
            (
                "Transform",
                (
                    self._tool("Move", "↕", "MoveTool", True),
                    self._tool("Rotate", "⟳", "RotateTool"),
                    self._tool("Scale", "◇", "ScaleTool"),
                    self._tool("Mirror", "⇋", "MirrorTool"),
                ),
            ),
            (
                "Edit",
                (
                    self._tool("Trim", "✂", "TrimTool", True),
                    self._tool("Extend", "⟶", "ExtendTool"),
                    self._tool("Offset", "∥", "OffsetTool"),
                    self._tool("Fillet", "⌒", "FilletTool"),
                    self._tool("Chamfer", "⟍", "ChamferTool"),
                ),
            ),
            (
                "Duplicate",
                (
                    self._tool("Copy", "⧉", "CopyTool"),
                    self._tool("Array", "▦", "ArrayTool"),
                ),
            ),
            (
                "History",
                (
                    self._command("Undo", "↶", "Undo the previous command.", self._undo),
                    self._command("Redo", "↷", "Redo the next command.", self._redo),
                ),
            ),
        )

    def _three_d_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return 3D modeling ribbon groups."""

        return (
            (
                "Primitives",
                (
                    self._tool("Box", "□", "BoxPrimitiveTool", True),
                    self._tool("Cube", "▣", "CubePrimitiveTool"),
                    self._tool("Plane", "▱", "PlanePrimitiveTool"),
                    self._tool("Cylinder", "◫", "CylinderPrimitiveTool"),
                    self._tool("Cone", "△", "ConePrimitiveTool"),
                    self._tool("Sphere", "●", "SpherePrimitiveTool"),
                    self._tool("Torus", "◎", "TorusPrimitiveTool"),
                    self._tool("Pyramid", "▲", "PyramidPrimitiveTool"),
                    self._tool("Prism", "⬢", "PrismPrimitiveTool"),
                    self._tool("Capsule", "⬤", "CapsulePrimitiveTool"),
                ),
            ),
            (
                "Solids",
                (
                    self._tool("Extrude", "⤴", "ExtrudeTool", True),
                    self._tool("Revolve", "⭮", "RevolveTool", True),
                    self._tool("Sweep", "⤳", "SweepTool"),
                    self._tool("Loft", "≋", "LoftTool"),
                ),
            ),
            (
                "Boolean",
                (
                    self._command("Union", "∪", "Boolean union.", lambda: self._boolean("union")),
                    self._command("Subtract", "−", "Boolean subtract.", lambda: self._boolean("subtract")),
                    self._command("Intersect", "∩", "Boolean intersect.", lambda: self._boolean("intersect")),
                ),
            ),
        )

    def _bim_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return BIM coordination ribbon groups."""

        return (
            (
                "Coordination",
                (
                    self._panel("References", "R", "reference_browser", True),
                    self._panel("Ref Layers", "L", "reference_layers"),
                    self._panel("Coordination", "C", "coordination"),
                ),
            ),
            (
                "Clash",
                (
                    self._panel("Clash Manager", "!", "clash_manager", True),
                    self._panel("Dashboard", "▦", "clash_dashboard"),
                    self._panel("BCF Topics", "B", "bcf_topic_browser"),
                ),
            ),
        )

    def _analyze_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return analysis ribbon groups."""

        return (
            (
                "Inspection",
                (
                    self._command("Fit View", "F", "Fit visible drawing.", self._fit_view, True),
                    self._command("Zoom Extents", "Z", "Zoom to drawing extents.", self._zoom_extents),
                    self._panel("Constraints", "C", "constraint_manager"),
                    self._panel("Selection Sets", "S", "selection_sets"),
                ),
            ),
        )

    def _fabrication_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return fabrication ribbon groups."""

        return (
            (
                "Machine",
                (
                    self._machine("Profile", "M", self._machine_profile, True),
                    self._machine("Create Job", "J", self._create_job),
                    self._machine("Toolpath", "T", self._generate_toolpath),
                    self._machine("Simulate", "▶", self._simulate),
                ),
            ),
            (
                "Output",
                (
                    self._machine("Post", "P", self._post_process),
                    self._machine("Export", "E", self._machine_export),
                    self._machine("Queue", "Q", self._queue_job),
                    self._machine("Execute", "▷", self._execute_job),
                    self._machine("Pause", "Ⅱ", self._pause),
                    self._machine("Resume", "▶", self._resume),
                    self._machine("Cancel", "×", self._cancel_job),
                    self._machine("Diagnostics", "?", self._machine_diagnostics),
                ),
            ),
        )

    def _ai_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return AI infrastructure ribbon groups."""

        return (
            (
                "Context",
                (
                    self._ai("Capture", "C", self._capture_context, True),
                    self._ai("New Session", "N", self._new_ai_session),
                    self._ai("Diagnostics", "?", self._ai_diagnostics),
                ),
            ),
            (
                "Prompt",
                (
                    self._ai("Validate", "✓", self._validate_prompt),
                    self._ai("Queue", "Q", self._queue_prompt),
                    self._ai("Cancel", "×", self._cancel_ai_task),
                    self._ai("Retry", "↻", self._retry_ai_task),
                    self._ai("Providers", "P", self._validate_providers),
                ),
            ),
        )

    def _view_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return view ribbon groups."""

        return (
            (
                "Viewport",
                (
                    self._command("2D View", "2D", "Switch to 2D view.", self._show_2d_view, True),
                    self._command("3D View", "3D", "Switch to 3D view.", self._show_3d_view, True),
                    self._command("Fit View", "F", "Fit visible drawing.", self._fit_view),
                    self._command("Zoom Extents", "Z", "Zoom to extents.", self._zoom_extents),
                ),
            ),
            (
                "Layout",
                (
                    self._command("Focus", "◉", "Enter focus mode.", self._focus_mode),
                    self._command("Presentation", "□", "Enter presentation mode.", self._presentation_mode),
                    self._command("Reset Layout", "↺", "Reset workspace layout.", self._reset_layout),
                ),
            ),
        )

    def _manage_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return manager ribbon groups."""

        return (
            (
                "Project",
                (
                    self._panel("Explorer", "E", "explorer", True),
                    self._panel("Project", "P", "project_manager"),
                ),
            ),
            (
                "CAD Managers",
                (
                    self._panel("Layers", "L", "layer_manager", True),
                    self._panel("Dimensions", "D", "dimension_manager"),
                    self._panel("Patterns", "H", "pattern_manager"),
                    self._panel("Blocks", "B", "block_manager"),
                    self._panel("Groups", "G", "group_manager"),
                ),
            ),
        )

    def _command(
        self,
        text: str,
        icon: str,
        tooltip: str,
        callback: Callable[[], None],
        large: bool = False,
    ) -> RibbonCommand:
        """Create a generic ribbon command definition."""

        return RibbonCommand(text, icon, tooltip, callback, large)

    def _tool(
        self,
        text: str,
        icon: str,
        tool_name: str,
        large: bool = False,
    ) -> RibbonCommand:
        """Create a tool activation command definition."""

        return self._command(
            text,
            icon,
            f"Activate {text}.",
            lambda name=tool_name: self.tool_manager.activate(name),
            large,
        )

    def _panel(
        self,
        text: str,
        icon: str,
        panel_id: str,
        large: bool = False,
    ) -> RibbonCommand:
        """Create an on-demand panel command definition."""

        return self._command(
            text,
            icon,
            f"Open {text}.",
            lambda target=panel_id: self._route_action(f"panel:{target}"),
            large,
        )

    def _ai(
        self,
        text: str,
        icon: str,
        callback: Callable[[], None],
        large: bool = False,
    ) -> RibbonCommand:
        """Create an AI command definition."""

        return self._command(text, icon, f"AI: {text}.", callback, large)

    def _machine(
        self,
        text: str,
        icon: str,
        callback: Callable[[], None],
        large: bool = False,
    ) -> RibbonCommand:
        """Create a fabrication command definition."""

        return self._command(text, icon, f"Machine/CAM: {text}.", callback, large)

    def _app(self):
        """Return the active CAD application facade when available."""

        return getattr(self.tool_manager, "app", None)

    def _workspace(self):
        """Return the active workspace when available."""

        app = self._app()
        return getattr(app, "workspace", None)

    def _main_window(self):
        """Return the owning main window when available."""

        return getattr(self.tool_manager, "main_window", None)

    def _route_action(self, action_id: str) -> None:
        """Route a shell action through the main window controller."""

        main_window = self._main_window()
        controller = getattr(main_window, "workspace_connection_controller", None)
        if controller is not None:
            controller.route_action(action_id)

    def _status(self, message: str) -> None:
        """Show status text through the active application shell."""

        main_window = self._main_window()
        status_bar = getattr(main_window, "studio_status_bar", None)
        if status_bar is not None:
            status_bar.show_status_text(message)

    def _save(self) -> None:
        """Save the current project."""

        app = self._app()
        if app is None:
            return
        if app.project_path is None:
            self._save_as()
            return
        app.save_project()

    def _save_as(self) -> None:
        """Save the current project to a chosen path."""

        app = self._app()
        if app is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Kinematics Studio Project",
            "",
            "Kinematics Studio Project (*.ksproj)",
        )
        if path:
            app.save_project(path)

    def _open(self) -> None:
        """Open an existing project."""

        app = self._app()
        if app is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Kinematics Studio Project",
            "",
            "Kinematics Studio Project (*.ksproj)",
        )
        if path:
            app.open_project(path)

    def _new_blank(self) -> None:
        """Create a blank project."""

        self._new_project(ProjectTemplateManager.BLANK)

    def _new_architectural(self) -> None:
        """Create an architectural project."""

        self._new_project(ProjectTemplateManager.ARCHITECTURAL)

    def _new_mechanical(self) -> None:
        """Create a mechanical project."""

        self._new_project(ProjectTemplateManager.MECHANICAL)

    def _new_project(self, template_name: str) -> None:
        """Create a project from a template."""

        app = self._app()
        if app is not None:
            app.new_project(template_name)

    def _toggle_autosave(self) -> None:
        """Toggle autosave on the application facade."""

        app = self._app()
        if app is None:
            return
        if app.autosave.enabled:
            app.autosave.stop()
            self._status("Autosave disabled.")
        else:
            app.autosave.start()
            self._status("Autosave enabled.")

    def _recover(self) -> None:
        """Recover an autosave project when available."""

        app = self._app()
        if app is not None and app.has_recovery():
            app.recover_project()

    def _export(self, format_name: str, file_filter: str) -> None:
        """Export the active project."""

        app = self._app()
        if app is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {format_name.upper()}",
            "",
            file_filter,
        )
        if path:
            if not path.lower().endswith(f".{format_name}"):
                path = f"{path}.{format_name}"
            app.export_project(path, format_name)

    def _import_3d(self) -> None:
        """Import an external 3D reference."""

        app = self._app()
        if app is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import 3D Reference",
            "",
            "3D References (*.obj *.stl *.ply *.off *.gltf *.glb *.fbx *.3ds *.step *.stp *.iges *.igs)",
        )
        if not path:
            return

        remembered = app.workspace.project_settings.get("import_options", {})
        dialog = ImportOptionsDialog(
            self,
            app.workspace.import_manager.last_result
            and getattr(app.workspace.import_manager.last_result, "settings", None)
            or None,
            path,
        )
        if remembered:
            from engine.import3d import ImportSettings

            dialog.set_settings(ImportSettings.from_dict(remembered))

        if dialog.exec() != dialog.Accepted:
            return

        settings = dialog.settings()
        app.workspace.import_manager.create_reference(
            app.workspace,
            path,
            None,
            settings,
        )
        if settings.remember_settings:
            app.workspace.project_settings["import_options"] = settings.to_dict()

    def _import_cad_exchange(self) -> None:
        """Import professional CAD exchange references."""

        app = self._app()
        if app is None:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import CAD Exchange",
            "",
            "CAD Exchange (*.skp *.3dm *.step *.stp *.brep *.iges *.igs *.sat *.stl *.obj *.fbx *.abc)",
        )
        if not path:
            return

        settings = None
        remembered = app.workspace.import_manager.adapter_settings.get("cad_import", {})
        if remembered:
            from engine.import3d import ImportSettings

            settings = ImportSettings.from_dict(remembered)

        dialog = ExchangeImportDialog(self, app.workspace, path, settings)
        if dialog.exec() != dialog.Accepted:
            return

        import_settings = dialog.settings()
        is_occ_exchange = Path(path).suffix.lower() in (".step", ".stp", ".brep")

        if is_occ_exchange:
            app.workspace.command_manager.execute(
                ImportOCCShapeCommand(app.engine, app.workspace, path)
            )
        else:
            app.workspace.import_manager.create_reference(
                app.workspace,
                path,
                None,
                import_settings,
            )

        profile = {
            "units": import_settings.units,
            "scale": import_settings.scale,
            "up_axis": import_settings.up_axis,
            "forward_axis": import_settings.forward_axis,
        }
        app.workspace.command_manager.execute(
            SaveExchangeProfileCommand(
                app.workspace,
                dialog.profile_name(),
                profile,
            )
        )
        if import_settings.remember_settings:
            before = dict(
                app.workspace.import_manager.adapter_settings.get("cad_import", {})
            )
            app.workspace.command_manager.execute(
                UpdateExchangeSettingsCommand(
                    app.workspace,
                    "cad_import",
                    before,
                    import_settings.to_dict(),
                )
            )

    def _export_cad_exchange(self) -> None:
        """Export professional CAD exchange data."""

        app = self._app()
        if app is None:
            return
        dialog = ExchangeExportDialog(self, app.workspace)
        if dialog.exec() != dialog.Accepted:
            return

        format_name = dialog.format_name()
        extension = "step" if format_name == "step" else format_name
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {format_name.upper()}",
            "",
            f"{format_name.upper()} Exchange (*.{extension})",
        )
        if not path:
            return
        if not path.lower().endswith(f".{extension}"):
            path = f"{path}.{extension}"

        report = app.workspace.import_manager.validation_manager.validate_workspace(
            app.workspace,
            format_name,
        )
        app.workspace.command_manager.execute(
            StoreExchangeValidationReportCommand(app.workspace, report)
        )
        if format_name in ("step", "brep"):
            app.engine.export_model(path)
        else:
            app.export_project(path, format_name)

        before = dict(app.workspace.import_manager.adapter_settings.get("cad_export", {}))
        app.workspace.command_manager.execute(
            UpdateExchangeSettingsCommand(
                app.workspace,
                "cad_export",
                before,
                dialog.profile_settings(),
            )
        )

    def _show_validation_report(self) -> None:
        """Show the latest import/export validation report."""

        app = self._app()
        if app is None:
            return
        panel = ExchangeValidationReportPanel(
            self,
            app.workspace.import_manager.validation_manager.last_report,
        )
        panel.exec()

    def _undo(self) -> None:
        """Undo the latest command."""

        workspace = self._workspace()
        if workspace is not None:
            workspace.command_manager.undo()

    def _redo(self) -> None:
        """Redo the latest command."""

        workspace = self._workspace()
        if workspace is not None:
            workspace.command_manager.redo()

    def _fit_view(self) -> None:
        """Fit the active 2D canvas view."""

        canvas = getattr(self.tool_manager, "canvas", None)
        if canvas is not None:
            canvas.fit_view()

    def _zoom_extents(self) -> None:
        """Zoom the active 2D canvas to extents."""

        canvas = getattr(self.tool_manager, "canvas", None)
        if canvas is not None:
            canvas.zoom_extents()

    def _show_2d_view(self) -> None:
        """Switch to the 2D viewport."""

        self._route_action("view_2d")

    def _show_3d_view(self) -> None:
        """Switch to the 3D viewport."""

        self._route_action("view_3d")

    def _focus_mode(self) -> None:
        """Enter focus mode."""

        self._route_action("focus_mode")

    def _presentation_mode(self) -> None:
        """Enter presentation mode."""

        self._route_action("presentation_mode")

    def _reset_layout(self) -> None:
        """Reset workspace layout."""

        self._route_action("reset_workspace_layout")

    def _boolean(self, operation: str) -> None:
        """Execute a Boolean operation on two selected OCC solids."""

        app = self._app()
        workspace = self._workspace()
        engine = getattr(app, "engine", None)
        if app is None or workspace is None or engine is None:
            return

        shapes = getattr(getattr(engine, "occ", None), "shapes", [])
        selected = [
            item
            for item in list(workspace.selection.selected)
            if item in shapes
        ]
        if len(selected) != 2:
            self._status("Select exactly two OCC solids for Boolean operation.")
            return

        workspace.command_manager.execute(
            OCCBooleanCommand(engine, workspace, operation, selected[0], selected[1])
        )
        self._status(f"Boolean {operation} completed.")

    def _ai_engine(self):
        """Return the active AI engine when available."""

        app = self._app()
        return getattr(getattr(app, "engine", None), "ai_engine", None)

    def _execute_ai(self, command, message: str) -> None:
        """Execute an AI command through the workspace command manager."""

        workspace = self._workspace()
        if workspace is None or command is None:
            return
        workspace.command_manager.execute(command)
        self._status(message)

    def _capture_context(self) -> None:
        """Capture AI project context."""

        self._execute_ai(
            CaptureAIContextCommand(
                self._ai_engine(),
                self._workspace(),
                "AI Ribbon Context",
            ),
            "AI context captured.",
        )

    def _new_ai_session(self) -> None:
        """Create an AI session."""

        self._execute_ai(
            CreateAISessionCommand(
                self._ai_engine(),
                self._workspace(),
                "AI Ribbon Session",
            ),
            "AI session created.",
        )

    def _validate_prompt(self) -> None:
        """Validate the default AI prompt."""

        self._execute_ai(
            ValidateAIPromptCommand(
                self._ai_engine(),
                self._workspace(),
                self._default_prompt(),
                capability="chat",
            ),
            "AI prompt validation completed.",
        )

    def _queue_prompt(self) -> None:
        """Queue the default AI prompt."""

        self._execute_ai(
            SubmitAIPromptCommand(
                self._ai_engine(),
                self._workspace(),
                self._default_prompt(),
                capability="chat",
                background=True,
            ),
            "AI prompt queued.",
        )

    def _cancel_ai_task(self) -> None:
        """Cancel the latest AI task."""

        task = self._latest_ai_task()
        if task is None:
            self._status("No AI task is available to cancel.")
            return
        self._execute_ai(
            CancelAITaskCommand(self._ai_engine(), self._workspace(), task.id),
            "AI task cancellation requested.",
        )

    def _retry_ai_task(self) -> None:
        """Retry the latest AI task."""

        task = self._latest_ai_task()
        if task is None:
            self._status("No AI task is available to retry.")
            return
        self._execute_ai(
            RetryAIPromptCommand(self._ai_engine(), self._workspace(), task.id),
            "AI task retry submitted.",
        )

    def _validate_providers(self) -> None:
        """Validate AI providers."""

        self._execute_ai(
            ValidateAIProvidersCommand(self._ai_engine(), self._workspace()),
            "AI provider validation completed.",
        )

    def _ai_diagnostics(self) -> None:
        """Capture AI diagnostics."""

        self._execute_ai(
            CaptureAIDiagnosticsCommand(self._ai_engine(), self._workspace()),
            "AI diagnostics captured.",
        )

    def _latest_ai_task(self):
        """Return the latest AI runtime task."""

        runtime = getattr(self._ai_engine(), "runtime", None)
        tasks = list(getattr(runtime, "tasks", {}).values())
        return tasks[-1] if tasks else None

    def _default_prompt(self) -> str:
        """Return the default engineering AI prompt."""

        return "Review the current project context and report infrastructure readiness."

    def _execute_machine(self, command, message: str) -> None:
        """Execute a Machine/CAM command through the command manager."""

        workspace = self._workspace()
        if workspace is None or command is None:
            return
        workspace.command_manager.execute(command)
        self._status(message)

    def _machine_profile(self) -> None:
        """Create or activate a machine profile."""

        self._execute_machine(
            CreateMachineProfileCommand(self._workspace()),
            "Machine profile ready.",
        )

    def _create_job(self) -> None:
        """Create a manufacturing job."""

        self._execute_machine(
            CreateManufacturingJobCommand(self._workspace()),
            "Manufacturing job created.",
        )

    def _generate_toolpath(self) -> None:
        """Generate a manufacturing toolpath."""

        self._execute_machine(
            GenerateToolpathCommand(self._workspace()),
            "Toolpath generated.",
        )

    def _simulate(self) -> None:
        """Run manufacturing simulation."""

        self._execute_machine(
            SimulateManufacturingJobCommand(self._workspace()),
            "Manufacturing simulation completed.",
        )

    def _post_process(self) -> None:
        """Post process the manufacturing job."""

        self._execute_machine(
            PostProcessManufacturingJobCommand(self._workspace()),
            "G-code generated.",
        )

    def _machine_export(self) -> None:
        """Export the manufacturing program."""

        self._execute_machine(
            ExportManufacturingJobCommand(self._workspace()),
            "Manufacturing program exported.",
        )

    def _queue_job(self) -> None:
        """Queue the manufacturing job."""

        self._execute_machine(
            QueueManufacturingJobCommand(self._workspace()),
            "Manufacturing job queued.",
        )

    def _execute_job(self) -> None:
        """Execute the manufacturing job."""

        self._execute_machine(
            ExecuteManufacturingJobCommand(self._workspace()),
            "Manufacturing job execution started.",
        )

    def _pause(self) -> None:
        """Pause the manufacturing job."""

        self._execute_machine(
            PauseManufacturingJobCommand(self._workspace()),
            "Manufacturing job paused.",
        )

    def _resume(self) -> None:
        """Resume the manufacturing job."""

        self._execute_machine(
            ResumeManufacturingJobCommand(self._workspace()),
            "Manufacturing job resumed.",
        )

    def _cancel_job(self) -> None:
        """Cancel the manufacturing job."""

        self._execute_machine(
            CancelManufacturingJobCommand(self._workspace()),
            "Manufacturing job cancelled.",
        )

    def _machine_diagnostics(self) -> None:
        """Capture Machine/CAM diagnostics."""

        self._execute_machine(
            CaptureMachineDiagnosticsCommand(self._workspace()),
            "Machine/CAM diagnostics captured.",
        )

    def _apply_style(self) -> None:
        """Apply the dark professional ribbon theme."""

        self.setStyleSheet(
            """
            QWidget#Ribbon {
                background-color: #1a1f27;
                border-bottom: 1px solid #2a2f38;
            }

            QTabWidget#RibbonTabs::pane {
                background-color: #1a1f27;
                border: none;
                border-top: 1px solid #2a2f38;
            }

            QTabBar::tab {
                background-color: #171b22;
                color: #aeb7c4;
                padding: 5px 14px;
                margin: 0;
                border: none;
                min-height: 22px;
                font-size: 12px;
                font-weight: 600;
            }

            QTabBar::tab:selected {
                background-color: #222936;
                color: #ffffff;
                border-bottom: 2px solid #3f8cff;
            }

            QTabBar::tab:hover {
                background-color: #26303c;
                color: #ffffff;
            }

            QScrollArea#RibbonScrollArea {
                background-color: transparent;
                border: none;
            }

            QFrame#RibbonGroup {
                background-color: #1d222a;
                border: 1px solid #2a2f38;
                border-radius: 4px;
            }

            QLabel#RibbonGroupTitle {
                color: #8f9aaa;
                font-size: 10px;
                font-weight: 600;
                padding-top: 1px;
            }

            QPushButton#RibbonButton,
            QPushButton#RibbonButtonLarge {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                color: #d7dde7;
                font-size: 10px;
                font-weight: 600;
                padding: 3px 5px;
                text-align: left;
            }

            QPushButton#RibbonButtonLarge {
                text-align: center;
            }

            QPushButton#RibbonButton:hover,
            QPushButton#RibbonButtonLarge:hover {
                background-color: #26303c;
                border-color: #3f8cff;
                color: #ffffff;
            }

            QPushButton#RibbonButton:pressed,
            QPushButton#RibbonButtonLarge:pressed {
                background-color: #2563eb;
                border-color: #78b7ff;
                color: #ffffff;
            }

            QPushButton#RibbonButton:disabled,
            QPushButton#RibbonButtonLarge:disabled {
                color: #666d78;
                background-color: #181b21;
                border-color: #242933;
            }

            QScrollBar:horizontal {
                background: #1a1f27;
                height: 7px;
            }

            QScrollBar::handle:horizontal {
                background: #3a4350;
                border-radius: 3px;
                min-width: 32px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #4b5665;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
            """
        )
