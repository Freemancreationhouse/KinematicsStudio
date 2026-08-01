from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QSize, QStringListModel, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class RibbonCommand:
    """Definition for a command displayed in the professional ribbon."""

    text: str
    icon: str
    tooltip: str
    callback: Callable[[], None]
    large: bool = False
    group: str = ""
    search_terms: tuple[str, ...] = ()


class RibbonButton(QPushButton):
    """Compact engineering ribbon button with consistent icon geometry."""

    def __init__(self, command: RibbonCommand, parent: QWidget | None = None) -> None:
        """Create a command button from an immutable command definition."""

        super().__init__(command.text, parent)

        self._command = command
        self._base_text = command.text
        self.setObjectName("RibbonButtonLarge" if command.large else "RibbonButton")
        self.setToolTip(command.tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(self._icon(command.icon, command.large))
        self.setIconSize(QSize(24, 24) if command.large else QSize(16, 16))
        self.setMinimumHeight(48 if command.large else 24)
        self.setMaximumHeight(52 if command.large else 26)
        self.setMinimumWidth(64 if command.large else 72)
        self.setMaximumWidth(78 if command.large else 110)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clicked.connect(lambda checked=False: command.callback())

    def set_compact(self, compact: bool) -> None:
        """Collapse secondary labels while keeping command affordance visible."""

        if self._command.large:
            self.setText(self._base_text)
            self.setMinimumWidth(62 if compact else 64)
            return

        self.setText("" if compact else self._base_text)
        self.setMinimumWidth(30 if compact else 72)
        self.setMaximumWidth(34 if compact else 110)

    def _icon(self, glyph: str, large: bool) -> QIcon:
        """Create a monochrome technical icon from a compact glyph."""

        size = 24 if large else 20
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#D7DDE7"), 1.4))
        font = painter.font()
        font.setFamily("Segoe UI")
        font.setPixelSize(13 if large else 11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, glyph)
        painter.end()

        return QIcon(pixmap)


class RibbonGroup(QFrame):
    """Titled ribbon group with compact controls and subtle separators."""

    def __init__(
        self,
        title: str,
        commands: tuple[RibbonCommand, ...],
        parent: QWidget | None = None,
    ) -> None:
        """Create a dense, professional command group."""

        super().__init__(parent)

        self._buttons: list[RibbonButton] = []
        self.setObjectName("RibbonGroup")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 4, 8, 3)
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
            self._buttons.append(button)
            if command.large:
                command_layout.addWidget(button, 0, large_column, 2, 1)
                large_column += 1
                small_column = max(small_column, large_column)
                continue

            command_layout.addWidget(button, small_row, small_column)
            small_row += 1
            if small_row >= 2:
                small_row = 0
                small_column += 1

        title_label = QLabel(title, self)
        title_label.setObjectName("RibbonGroupTitle")
        title_label.setAlignment(Qt.AlignCenter)
        root.addWidget(title_label)

    def set_compact(self, compact: bool) -> None:
        """Apply compact mode to all contained command buttons."""

        for button in self._buttons:
            button.set_compact(compact)


class RibbonPage(QWidget):
    """Scrollable ribbon page containing professional command groups."""

    def __init__(
        self,
        groups: tuple[tuple[str, tuple[RibbonCommand, ...]], ...],
        parent: QWidget | None = None,
    ) -> None:
        """Create a page from group definitions."""

        super().__init__(parent)

        self._groups: list[RibbonGroup] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        for title, commands in groups:
            group = RibbonGroup(title, commands, self)
            self._groups.append(group)
            layout.addWidget(group)

        layout.addStretch(1)

    def set_compact(self, compact: bool) -> None:
        """Apply responsive compact mode to the page."""

        for group in self._groups:
            group.set_compact(compact)


class Ribbon(QWidget):
    """World-class engineering ribbon for Kinematics Studio."""

    HIDDEN_TABS: set[str] = set()
    CONTEXT_TAB_TITLES = {"Mesh Tools", "Curve Tools"}

    actionTriggered = Signal(str)
    toolSelected = Signal(str)

    def __init__(self, app) -> None:
        """Create a presentation-first ribbon using existing routing signals."""

        super().__init__()

        self._app = app
        self._commands: dict[str, RibbonCommand] = {}
        self._pages: list[RibbonPage] = []
        self._context_signature: tuple[str, ...] = ()

        self.setObjectName("Ribbon")
        self.setMaximumHeight(128)
        self.setMinimumHeight(116)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._title_bar())

        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("RibbonTabs")
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        layout.addWidget(self.tabs)

        self._build_tabs()
        self._configure_search()
        self._apply_style()

        self._context_timer = QTimer(self)
        self._context_timer.setInterval(180)
        self._context_timer.timeout.connect(self._sync_context_tabs)
        self._context_timer.start()

    def resizeEvent(self, event) -> None:
        """Adapt ribbon density to available width."""

        super().resizeEvent(event)
        compact = self.width() < 1320
        for page in self._pages:
            page.set_compact(compact)

    def _title_bar(self) -> QWidget:
        """Create the title, quick access toolbar and ribbon search."""

        title_bar = QFrame(self)
        title_bar.setObjectName("RibbonTitleBar")
        title_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(8, 6, 8, 4)
        layout.setSpacing(8)

        product = QLabel("KINEMATICS STUDIO", title_bar)
        product.setObjectName("RibbonProductTitle")
        layout.addWidget(product)

        context = QLabel("Engineering Workspace", title_bar)
        context.setObjectName("RibbonProductContext")
        layout.addWidget(context)

        separator = QFrame(title_bar)
        separator.setObjectName("RibbonTitleSeparator")
        separator.setFrameShape(QFrame.VLine)
        layout.addWidget(separator)

        for command in self._quick_access_commands():
            button = RibbonButton(command, title_bar)
            button.setObjectName("QuickAccessButtonLarge" if command.large else "QuickAccessButton")
            layout.addWidget(button)

        layout.addStretch(1)

        self.search = QLineEdit(title_bar)
        self.search.setObjectName("RibbonSearch")
        self.search.setPlaceholderText("Search commands")
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(220)
        self.search.setMaximumWidth(320)
        self.search.returnPressed.connect(self._activate_search_text)
        layout.addWidget(self.search)

        return title_bar

    def _quick_access_commands(self) -> tuple[RibbonCommand, ...]:
        """Return always-visible Quick Access Toolbar commands."""

        return (
            self._command("New", "N", "Create a new project.", lambda: self._emit_action("project:new:blank"), True, "Quick Access"),
            self._command("Open", "O", "Open a project.", lambda: self._emit_action("project:open"), True, "Quick Access"),
            self._command("Save", "S", "Save the active project.", lambda: self._emit_action("project:save"), True, "Quick Access"),
            self._command("Undo", "U", "Undo the previous command.", lambda: self._emit_action("command:undo"), True, "Quick Access"),
            self._command("Redo", "R", "Redo the next command.", lambda: self._emit_action("command:redo"), True, "Quick Access"),
        )

    def _build_tabs(self) -> None:
        """Build primary workspace tabs in the approved Sprint 2 order."""

        self._add_tab("Home", self._home_groups())
        self._add_tab("Draw", self._draw_groups())
        self._add_tab("Modify", self._modify_groups())
        self._add_tab("View", self._view_groups())
        self._add_tab("Create", self._create_groups())
        self._add_tab("Analyze", self._analyze_groups())
        self._add_tab("Render", self._render_groups())
        self._add_tab("Machine", self._machine_groups())
        self._add_tab("AI", self._ai_groups())
        self._add_tab("Settings", self._settings_groups())

    def _add_tab(
        self,
        title: str,
        groups: tuple[tuple[str, tuple[RibbonCommand, ...]], ...],
    ) -> None:
        """Add a scrollable tab page."""

        if title in self.HIDDEN_TABS:
            return

        page = RibbonPage(groups, self.tabs)
        self._pages.append(page)
        scroll = QScrollArea(self.tabs)
        scroll.setObjectName("RibbonScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(page)
        self.tabs.addTab(scroll, title)

    def _configure_search(self) -> None:
        """Configure command search over existing ribbon commands."""

        labels = sorted(self._commands)
        self._search_model = QStringListModel(labels, self)
        self.search_completer = QCompleter(self._search_model, self)
        self.search_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_completer.setFilterMode(Qt.MatchContains)
        self.search_completer.activated.connect(self._activate_search_result)
        self.search.setCompleter(self.search_completer)

    def _home_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Home tab groups."""

        return (
            (
                "Project",
                (
                    self._action("New", "N", "project:new:blank", "Create a blank project.", True),
                    self._action("Open", "O", "project:open", "Open an existing project.", True),
                    self._action("Save", "S", "project:save", "Save the current project.", True),
                    self._action("Save As", "SA", "project:save_as", "Save to a new file."),
                ),
            ),
            (
                "Clipboard",
                (
                    self._action("Undo", "U", "command:undo", "Undo the previous command.", True),
                    self._action("Redo", "R", "command:redo", "Redo the next command.", True),
                ),
            ),
            (
                "Selection",
                (
                    self._action("Select", "SE", "select", "Return to Select."),
                    self._panel("Sets", "SS", "selection_sets"),
                    self._panel("Explorer", "EX", "explorer"),
                    self._panel("Layers", "LA", "layer_manager"),
                ),
            ),
        )

    def _draw_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Draw tab groups."""

        return (
            (
                "Draw",
                (
                    self._tool("Line", "LN", "LineTool"),
                    self._tool("Polyline", "PL", "PolylineTool"),
                    self._tool("Rectangle", "RC", "RectangleTool"),
                    self._tool("Circle", "CI", "CircleTool"),
                    self._tool("Arc", "AR", "ArcTool"),
                    self._tool("Ellipse", "EL", "EllipseTool"),
                    self._tool("Polygon", "PG", "PolygonTool"),
                    self._tool("Spline", "SP", "SplineTool"),
                ),
            ),
            (
                "Annotate",
                (
                    self._tool("Text", "TX", "TextTool"),
                    self._tool("MText", "MT", "MTextTool"),
                    self._tool("Leader", "LD", "LeaderTool"),
                    self._tool("Hatch", "HT", "HatchTool"),
                ),
            ),
            (
                "Dimensions",
                (
                    self._tool("Linear", "LI", "LinearDimensionTool"),
                    self._tool("Aligned", "AL", "AlignedDimensionTool"),
                    self._tool("Radius", "RA", "RadiusDimensionTool"),
                    self._tool("Diameter", "DI", "DiameterDimensionTool"),
                    self._tool("Angular", "AN", "AngularDimensionTool"),
                ),
            ),
        )

    def _modify_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Modify tab groups."""

        return (
            (
                "Transform",
                (
                    self._tool("Move", "MV", "MoveTool"),
                    self._tool("Rotate", "RT", "RotateTool"),
                    self._tool("Scale", "SC", "ScaleTool"),
                    self._tool("Mirror", "MR", "MirrorTool"),
                    self._tool("Copy", "CP", "CopyTool"),
                    self._tool("Array", "AY", "ArrayTool"),
                ),
            ),
            (
                "Edit",
                (
                    self._tool("Trim", "TR", "TrimTool"),
                    self._tool("Extend", "EX", "ExtendTool"),
                    self._tool("Offset", "OF", "OffsetTool"),
                    self._tool("Fillet", "FI", "FilletTool"),
                    self._tool("Chamfer", "CH", "ChamferTool"),
                ),
            ),
        )

    def _view_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return View tab groups."""

        return (
            (
                "Viewport",
                (
                    self._action("2D View", "2D", "view_2d", "Switch to 2D view."),
                    self._action("3D View", "3D", "view_3d", "Switch to 3D view."),
                    self._action("Home", "HM", "view:home", "Return cameras home."),
                    self._action("Fit", "FT", "view:fit", "Fit the current view."),
                    self._action("Extents", "ZE", "view:zoom_extents", "Zoom to extents."),
                    self._action("Selected", "ZS", "view:zoom_selected", "Zoom to selected objects."),
                ),
            ),
            (
                "Workspace",
                (
                    self._action("Focus", "FO", "focus_mode", "Enter focus mode."),
                    self._action("Present", "PR", "presentation_mode", "Enter presentation mode."),
                    self._action("Reset", "RS", "reset_workspace_layout", "Reset workspace layout."),
                ),
            ),
        )

    def _create_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Create tab groups."""

        return (
            (
                "Primitives",
                (
                    self._tool("Box", "BX", "BoxPrimitiveTool"),
                    self._tool("Cube", "CB", "CubePrimitiveTool"),
                    self._tool("Plane", "PN", "PlanePrimitiveTool"),
                    self._tool("Cylinder", "CY", "CylinderPrimitiveTool"),
                    self._tool("Cone", "CN", "ConePrimitiveTool"),
                    self._tool("Sphere", "SH", "SpherePrimitiveTool"),
                    self._tool("Torus", "TO", "TorusPrimitiveTool"),
                    self._tool("Pyramid", "PY", "PyramidPrimitiveTool"),
                    self._tool("Prism", "PS", "PrismPrimitiveTool"),
                    self._tool("Capsule", "CA", "CapsulePrimitiveTool"),
                ),
            ),
            (
                "Solids",
                (
                    self._tool("Extrude", "EX", "ExtrudeTool"),
                    self._tool("Revolve", "RV", "RevolveTool"),
                    self._tool("Sweep", "SW", "SweepTool"),
                    self._tool("Loft", "LF", "LoftTool"),
                ),
            ),
            (
                "Boolean",
                (
                    self._action("Union", "UN", "boolean:union", "Boolean union."),
                    self._action("Subtract", "SB", "boolean:subtract", "Boolean subtract."),
                    self._action("Intersect", "IN", "boolean:intersect", "Boolean intersect."),
                ),
            ),
        )

    def _analyze_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Analyze tab groups."""

        return (
            (
                "Inspection",
                (
                    self._panel("Constraints", "CS", "constraint_manager"),
                    self._panel("Selection Sets", "SS", "selection_sets"),
                    self._panel("References", "RF", "reference_browser"),
                    self._panel("Reference Layers", "RL", "reference_layers"),
                ),
            ),
            (
                "Coordination",
                (
                    self._panel("Coordination", "CO", "coordination"),
                    self._panel("Clash Manager", "CL", "clash_manager"),
                    self._panel("Clash Dashboard", "CD", "clash_dashboard"),
                    self._panel("BCF Topics", "BC", "bcf_topic_browser"),
                ),
            ),
        )

    def _render_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Render tab groups."""

        return (
            (
                "Camera",
                (
                    self._action("Home", "HM", "view:home", "Return cameras home."),
                    self._action("Extents", "ZE", "view:zoom_extents", "Frame the model."),
                    self._action("Selected", "ZS", "view:zoom_selected", "Frame selected objects."),
                ),
            ),
            (
                "Presentation",
                (
                    self._action("Focus", "FO", "focus_mode", "Enter focus mode."),
                    self._action("Present", "PR", "presentation_mode", "Enter presentation mode."),
                    self._action("Reset", "RS", "reset_workspace_layout", "Reset layout."),
                ),
            ),
        )

    def _machine_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Machine tab groups."""

        return (
            (
                "Job",
                (
                    self._machine("Profile", "MP", "profile"),
                    self._machine("Create Job", "CJ", "create_job"),
                    self._machine("Toolpath", "TP", "generate_toolpath"),
                    self._machine("Simulate", "SM", "simulate"),
                ),
            ),
            (
                "Output",
                (
                    self._machine("Post", "PP", "post_process"),
                    self._machine("Export", "EX", "export"),
                    self._machine("Queue", "QU", "queue_job"),
                    self._machine("Execute", "GO", "execute_job"),
                    self._machine("Pause", "PA", "pause"),
                    self._machine("Resume", "RE", "resume"),
                    self._machine("Cancel", "CA", "cancel_job"),
                    self._machine("Diagnostics", "DG", "diagnostics"),
                ),
            ),
        )

    def _ai_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return AI tab groups."""

        return (
            (
                "Context",
                (
                    self._ai("Capture", "CC", "capture_context"),
                    self._ai("New Session", "NS", "new_session"),
                    self._ai("Diagnostics", "DG", "diagnostics"),
                ),
            ),
            (
                "Prompt",
                (
                    self._ai("Validate", "VA", "validate_prompt"),
                    self._ai("Queue", "QU", "queue_prompt"),
                    self._ai("Cancel", "CA", "cancel_task"),
                    self._ai("Retry", "RT", "retry_task"),
                    self._ai("Providers", "PV", "validate_providers"),
                ),
            ),
        )

    def _settings_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return Settings tab groups."""

        return (
            (
                "Project",
                (
                    self._panel("Project", "PJ", "project_manager"),
                    self._panel("Explorer", "EX", "explorer"),
                    self._panel("Layers", "LA", "layer_manager"),
                    self._panel("Dimensions", "DM", "dimension_manager"),
                ),
            ),
            (
                "Resources",
                (
                    self._panel("Patterns", "PT", "pattern_manager"),
                    self._panel("Blocks", "BL", "block_manager"),
                    self._panel("Groups", "GR", "group_manager"),
                ),
            ),
        )

    def _mesh_context_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return context groups for selected mesh or solid entities."""

        return (
            (
                "Mesh Selection",
                (
                    self._action("Frame", "FR", "view:zoom_selected", "Frame selected mesh."),
                    self._tool("Move", "MV", "MoveTool"),
                    self._tool("Rotate", "RT", "RotateTool"),
                    self._tool("Scale", "SC", "ScaleTool"),
                    self._action("Properties", "PR", "panel:project_manager", "Open properties context."),
                ),
            ),
        )

    def _curve_context_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return context groups for selected curve entities."""

        return (
            (
                "Curve Selection",
                (
                    self._action("Frame", "FR", "view:zoom_selected", "Frame selected curve."),
                    self._tool("Move", "MV", "MoveTool"),
                    self._tool("Offset", "OF", "OffsetTool"),
                    self._tool("Trim", "TR", "TrimTool"),
                    self._tool("Extend", "EX", "ExtendTool"),
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
        group: str = "",
        search_terms: tuple[str, ...] = (),
    ) -> RibbonCommand:
        """Create and index a command definition."""

        command = RibbonCommand(text, icon, tooltip, callback, large, group, search_terms)
        self._register_command(command)
        return command

    def _action(
        self,
        text: str,
        icon: str,
        action_id: str,
        tooltip: str,
        large: bool = False,
    ) -> RibbonCommand:
        """Create an action-routed command definition."""

        return self._command(
            text,
            icon,
            tooltip,
            lambda current=action_id: self._emit_action(current),
            large,
            action_id.split(":", 1)[0].title(),
            (action_id,),
        )

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
            lambda name=tool_name: self._emit_tool(name),
            large,
            "Tools",
            (tool_name,),
        )

    def _panel(
        self,
        text: str,
        icon: str,
        panel_id: str,
        large: bool = False,
    ) -> RibbonCommand:
        """Create an on-demand panel command definition."""

        return self._action(text, icon, f"panel:{panel_id}", f"Open {text}.", large)

    def _ai(self, text: str, icon: str, action_id: str) -> RibbonCommand:
        """Create an AI command definition."""

        return self._action(text, icon, f"ai:{action_id}", f"AI: {text}.")

    def _machine(self, text: str, icon: str, action_id: str) -> RibbonCommand:
        """Create a Machine/CAM command definition."""

        return self._action(text, icon, f"machine:{action_id}", f"Machine/CAM: {text}.")

    def _register_command(self, command: RibbonCommand) -> None:
        """Register command aliases for ribbon search."""

        labels = {
            command.text,
            f"{command.text} - {command.group}" if command.group else command.text,
            *command.search_terms,
        }
        for label in labels:
            if label:
                self._commands[label] = command
        if hasattr(self, "_search_model"):
            self._search_model.setStringList(sorted(self._commands))

    def _activate_search_text(self) -> None:
        """Activate the current ribbon search text."""

        self._activate_search_result(self.search.text())

    def _activate_search_result(self, text: str) -> None:
        """Run the command selected from ribbon search."""

        query = text.strip()
        if not query:
            return

        command = self._commands.get(query)
        if command is None:
            normalized = query.casefold()
            for label, candidate in self._commands.items():
                if normalized in label.casefold():
                    command = candidate
                    break

        if command is None:
            return

        self.search.clear()
        command.callback()

    def _sync_context_tabs(self) -> None:
        """Show or hide context tabs based on the active selection."""

        selected = self._current_selection()
        signature = tuple(sorted(self._context_kinds(selected)))
        if signature == self._context_signature:
            return

        self._context_signature = signature
        self._remove_context_tabs()

        if "mesh" in signature:
            self._add_tab("Mesh Tools", self._mesh_context_groups())
        if "curve" in signature:
            self._add_tab("Curve Tools", self._curve_context_groups())

    def _remove_context_tabs(self) -> None:
        """Remove all visible context tabs."""

        for index in reversed(range(self.tabs.count())):
            title = self.tabs.tabText(index)
            if title in self.CONTEXT_TAB_TITLES:
                widget = self.tabs.widget(index)
                page = widget.widget() if isinstance(widget, QScrollArea) else None
                if page in self._pages:
                    self._pages.remove(page)
                self.tabs.removeTab(index)
                if widget is not None:
                    widget.deleteLater()

    def _context_kinds(self, selected: list[object]) -> set[str]:
        """Return context kinds represented by selected entities."""

        kinds: set[str] = set()
        for entity in selected:
            type_name = str(getattr(entity, "type_name", entity.__class__.__name__))
            if getattr(entity, "is_3d", False) or "Mesh" in type_name or "Solid" in type_name:
                kinds.add("mesh")
            if any(token in type_name for token in ("Line", "Curve", "Polyline", "Spline", "Arc", "Circle", "Ellipse")):
                kinds.add("curve")
        return kinds

    def _current_selection(self) -> list[object]:
        """Return the active selection for context-tab presentation."""

        workspace = getattr(self._app, "workspace", None)
        selection = getattr(workspace, "selection", None)
        selected = getattr(selection, "selected", [])
        if callable(selected):
            selected = selected()
        return list(selected or [])

    def _emit_action(self, action_id: str) -> None:
        """Emit a presentation action identifier for controller routing."""

        self.actionTriggered.emit(action_id)

    def _emit_tool(self, tool_name: str) -> None:
        """Emit a tool selection identifier for controller routing."""

        self.toolSelected.emit(tool_name)

    def _apply_style(self) -> None:
        """Apply the locked Sprint 2 engineering design language."""

        self.setStyleSheet(
            """
            QWidget#Ribbon {
                background-color: #2A2C31;
                border-bottom: 1px solid #1E1F22;
            }

            QFrame#RibbonTitleBar {
                background-color: #1E1F22;
                border-bottom: 1px solid #25272C;
            }

            QLabel#RibbonProductTitle {
                color: #F2F5F8;
                font-family: "Inter", "Segoe UI";
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#RibbonProductContext {
                color: #AEB6C2;
                font-family: "Inter", "Segoe UI";
                font-size: 11px;
                font-weight: 600;
            }

            QFrame#RibbonTitleSeparator {
                color: #3D4148;
                margin-left: 4px;
                margin-right: 4px;
            }

            QLineEdit#RibbonSearch {
                background-color: #25272C;
                border: 1px solid #3D4148;
                border-radius: 6px;
                color: #E3E8EF;
                font-family: "Inter", "Segoe UI";
                font-size: 11px;
                min-height: 24px;
                padding: 2px 8px;
            }

            QLineEdit#RibbonSearch:focus {
                border-color: #4FA3FF;
            }

            QPushButton#QuickAccessButton,
            QPushButton#QuickAccessButtonLarge {
                background-color: #25272C;
                border: 1px solid #3D4148;
                border-radius: 6px;
                color: #D7DDE7;
                font-family: "Inter", "Segoe UI";
                font-size: 10px;
                font-weight: 700;
                min-height: 26px;
                padding: 2px 6px;
            }

            QPushButton#QuickAccessButton:hover,
            QPushButton#QuickAccessButtonLarge:hover {
                background-color: #3D4148;
                border-color: #4FA3FF;
                color: #FFFFFF;
            }

            QPushButton#QuickAccessButton:pressed,
            QPushButton#QuickAccessButtonLarge:pressed {
                background-color: #3BA4F7;
                border-color: #4FA3FF;
                color: #FFFFFF;
            }

            QTabWidget#RibbonTabs::pane {
                background-color: #2A2C31;
                border: none;
                border-top: 1px solid #25272C;
            }

            QTabBar::tab {
                background-color: #25272C;
                color: #B7C0CC;
                font-family: "Inter", "Segoe UI";
                font-size: 11px;
                font-weight: 650;
                min-height: 22px;
                padding: 4px 12px;
                border: none;
            }

            QTabBar::tab:selected {
                background-color: #30333A;
                color: #FFFFFF;
                border-bottom: 2px solid #4FA3FF;
            }

            QTabBar::tab:hover {
                background-color: #3D4148;
                color: #FFFFFF;
            }

            QScrollArea#RibbonScrollArea {
                background-color: transparent;
                border: none;
            }

            QFrame#RibbonGroup {
                background-color: #30333A;
                border: 1px solid #3D4148;
                border-radius: 8px;
            }

            QLabel#RibbonGroupTitle {
                color: #9AA4B2;
                font-family: "Inter", "Segoe UI";
                font-size: 10px;
                font-weight: 700;
                padding-top: 1px;
            }

            QPushButton#RibbonButton,
            QPushButton#RibbonButtonLarge {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 6px;
                color: #D7DDE7;
                font-family: "Inter", "Segoe UI";
                font-size: 10px;
                font-weight: 650;
                padding: 2px 4px;
                text-align: left;
            }

            QPushButton#RibbonButtonLarge {
                text-align: center;
            }

            QPushButton#RibbonButton:hover,
            QPushButton#RibbonButtonLarge:hover {
                background-color: #3D4148;
                border-color: #4FA3FF;
                color: #FFFFFF;
            }

            QPushButton#RibbonButton:pressed,
            QPushButton#RibbonButtonLarge:pressed {
                background-color: #3BA4F7;
                border-color: #4FA3FF;
                color: #FFFFFF;
            }

            QScrollBar:horizontal {
                background: #25272C;
                height: 6px;
            }

            QScrollBar::handle:horizontal {
                background: #3D4148;
                border-radius: 3px;
                min-width: 32px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #4FA3FF;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0;
            }
            """
        )
