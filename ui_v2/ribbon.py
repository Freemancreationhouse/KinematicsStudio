from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


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
    actionTriggered = Signal(str)
    toolSelected = Signal(str)

    def __init__(self, app) -> None:
        """Create the presentation-only ribbon."""

        super().__init__()

        self.setObjectName("Ribbon")
        self.setMaximumHeight(138)
        self.setMinimumHeight(124)
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
        self._apply_style()

    def _build_tabs(self) -> None:
        """Build all production ribbon tabs."""

        self._add_tab("Home", self._project_groups())
        self._add_tab("Draw", self._draw_groups())
        self._add_tab("Modify", self._modify_groups())
        self._add_tab("View", self._view_groups())
        self._add_tab("Create", self._three_d_groups())
        self._add_tab("Analyze", self._analyze_groups())
        self._add_tab("Render", self._render_groups())
        self._add_tab("Machine", self._fabrication_groups())
        self._add_tab("AI", self._ai_groups())

    def _title_bar(self) -> QWidget:
        """Create the professional in-application title and quick access bar."""

        title_bar = QFrame(self)
        title_bar.setObjectName("RibbonTitleBar")
        title_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 6, 10, 5)
        layout.setSpacing(6)

        product = QLabel("KINEMATICS STUDIO", title_bar)
        product.setObjectName("RibbonProductTitle")
        layout.addWidget(product)

        context = QLabel("Professional Engineering Workspace", title_bar)
        context.setObjectName("RibbonProductContext")
        layout.addWidget(context)
        layout.addStretch(1)

        for command in self._quick_access_commands():
            button = QPushButton(command.text, title_bar)
            button.setObjectName("QuickAccessButton")
            button.setToolTip(command.tooltip)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, callback=command.callback: callback())
            layout.addWidget(button)

        return title_bar

    def _quick_access_commands(self) -> tuple[RibbonCommand, ...]:
        """Return quick access commands routed through presentation signals."""

        return (
            self._command("New", "N", "Create a new project.", lambda: self._emit_action("project:new:blank")),
            self._command("Open", "O", "Open project.", lambda: self._emit_action("project:open")),
            self._command("Save", "S", "Save project.", lambda: self._emit_action("project:save")),
            self._command("Undo", "↶", "Undo last command.", lambda: self._emit_action("command:undo")),
            self._command("Redo", "↷", "Redo next command.", lambda: self._emit_action("command:redo")),
            self._command("Settings", "⚙", "Open project settings.", lambda: self._emit_action("panel:project_manager")),
        )

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
                    self._command("New", "N", "Create a blank project.", lambda: self._emit_action("project:new:blank"), True),
                    self._command("Open", "O", "Open an existing project.", lambda: self._emit_action("project:open")),
                    self._command("Save", "S", "Save the current project.", lambda: self._emit_action("project:save")),
                    self._command("Save As", "⇧S", "Save the project to a new file.", lambda: self._emit_action("project:save_as")),
                ),
            ),
            (
                "Templates",
                (
                    self._command("Architectural", "A", "Create from architectural template.", lambda: self._emit_action("project:new:architectural")),
                    self._command("Mechanical", "M", "Create from mechanical template.", lambda: self._emit_action("project:new:mechanical")),
                    self._command("Recover", "R", "Recover the latest autosave.", lambda: self._emit_action("project:recover")),
                    self._command("Auto Save", "⟳", "Toggle autosave.", lambda: self._emit_action("project:toggle_autosave")),
                ),
            ),
            (
                "Import / Export",
                (
                    self._command("Import 3D", "I", "Import an external 3D reference.", lambda: self._emit_action("import:3d"), True),
                    self._command("Import CAD", "⇩", "Import professional CAD exchange data.", lambda: self._emit_action("import:cad_exchange")),
                    self._command("Export CAD", "⇧", "Export professional CAD exchange data.", lambda: self._emit_action("export:cad_exchange")),
                    self._command("Validate", "✓", "Show exchange validation report.", lambda: self._emit_action("exchange:show_validation_report")),
                    self._command("DXF", "D", "Export DXF drawing.", lambda: self._emit_action("export:dxf")),
                    self._command("SVG", "V", "Export SVG drawing.", lambda: self._emit_action("export:svg")),
                    self._command("PDF", "P", "Export PDF drawing.", lambda: self._emit_action("export:pdf")),
                    self._command("PNG", "G", "Export PNG image.", lambda: self._emit_action("export:png")),
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
                    self._command("Undo", "↶", "Undo the previous command.", lambda: self._emit_action("command:undo")),
                    self._command("Redo", "↷", "Redo the next command.", lambda: self._emit_action("command:redo")),
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
                    self._command("Union", "∪", "Boolean union.", lambda: self._emit_action("boolean:union")),
                    self._command("Subtract", "−", "Boolean subtract.", lambda: self._emit_action("boolean:subtract")),
                    self._command("Intersect", "∩", "Boolean intersect.", lambda: self._emit_action("boolean:intersect")),
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
                    self._command("Fit View", "F", "Fit visible drawing.", lambda: self._emit_action("view:fit"), True),
                    self._command("Zoom Extents", "Z", "Zoom to drawing extents.", lambda: self._emit_action("view:zoom_extents")),
                    self._panel("Constraints", "C", "constraint_manager"),
                    self._panel("Selection Sets", "S", "selection_sets"),
                ),
            ),
            *self._bim_groups(),
        )

    def _render_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return render and presentation workspace groups."""

        return (
            (
                "Camera",
                (
                    self._command("Home", "H", "Return cameras to home.", lambda: self._emit_action("view:home"), True),
                    self._command("Zoom Extents", "Z", "Fit the model.", lambda: self._emit_action("view:zoom_extents")),
                    self._command("Zoom Selected", "ZS", "Frame selected objects.", lambda: self._emit_action("view:zoom_selected")),
                ),
            ),
            (
                "Workspace",
                (
                    self._command("Focus", "◎", "Enter focus mode.", lambda: self._emit_action("focus_mode")),
                    self._command("Presentation", "□", "Enter presentation mode.", lambda: self._emit_action("presentation_mode")),
                    self._command("Reset", "↺", "Reset workspace layout.", lambda: self._emit_action("reset_workspace_layout")),
                ),
            ),
        )

    def _fabrication_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return fabrication ribbon groups."""

        return (
            (
                "Machine",
                (
                    self._machine("Profile", "M", lambda: self._emit_action("machine:profile"), True),
                    self._machine("Create Job", "J", lambda: self._emit_action("machine:create_job")),
                    self._machine("Toolpath", "T", lambda: self._emit_action("machine:generate_toolpath")),
                    self._machine("Simulate", "▶", lambda: self._emit_action("machine:simulate")),
                ),
            ),
            (
                "Output",
                (
                    self._machine("Post", "P", lambda: self._emit_action("machine:post_process")),
                    self._machine("Export", "E", lambda: self._emit_action("machine:export")),
                    self._machine("Queue", "Q", lambda: self._emit_action("machine:queue_job")),
                    self._machine("Execute", "▷", lambda: self._emit_action("machine:execute_job")),
                    self._machine("Pause", "Ⅱ", lambda: self._emit_action("machine:pause")),
                    self._machine("Resume", "▶", lambda: self._emit_action("machine:resume")),
                    self._machine("Cancel", "×", lambda: self._emit_action("machine:cancel_job")),
                    self._machine("Diagnostics", "?", lambda: self._emit_action("machine:diagnostics")),
                ),
            ),
        )

    def _ai_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return AI infrastructure ribbon groups."""

        return (
            (
                "Context",
                (
                    self._ai("Capture", "C", lambda: self._emit_action("ai:capture_context"), True),
                    self._ai("New Session", "N", lambda: self._emit_action("ai:new_session")),
                    self._ai("Diagnostics", "?", lambda: self._emit_action("ai:diagnostics")),
                ),
            ),
            (
                "Prompt",
                (
                    self._ai("Validate", "✓", lambda: self._emit_action("ai:validate_prompt")),
                    self._ai("Queue", "Q", lambda: self._emit_action("ai:queue_prompt")),
                    self._ai("Cancel", "×", lambda: self._emit_action("ai:cancel_task")),
                    self._ai("Retry", "↻", lambda: self._emit_action("ai:retry_task")),
                    self._ai("Providers", "P", lambda: self._emit_action("ai:validate_providers")),
                ),
            ),
        )

    def _view_groups(self) -> tuple[tuple[str, tuple[RibbonCommand, ...]], ...]:
        """Return view ribbon groups."""

        return (
            (
                "Viewport",
                (
                    self._command("2D View", "2D", "Switch to 2D view.", lambda: self._emit_action("view_2d"), True),
                    self._command("3D View", "3D", "Switch to 3D view.", lambda: self._emit_action("view_3d"), True),
                    self._command("Home", "H", "Return cameras to the home view.", lambda: self._emit_action("view:home")),
                    self._command("Fit View", "F", "Fit visible drawing.", lambda: self._emit_action("view:fit")),
                    self._command("Zoom Extents", "Z", "Zoom to extents.", lambda: self._emit_action("view:zoom_extents")),
                    self._command("Zoom Selected", "ZS", "Zoom to selected geometry.", lambda: self._emit_action("view:zoom_selected")),
                ),
            ),
            (
                "Layout",
                (
                    self._command("Focus", "◉", "Enter focus mode.", lambda: self._emit_action("focus_mode")),
                    self._command("Presentation", "□", "Enter presentation mode.", lambda: self._emit_action("presentation_mode")),
                    self._command("Reset Layout", "↺", "Reset workspace layout.", lambda: self._emit_action("reset_workspace_layout")),
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
            lambda name=tool_name: self._emit_tool(name),
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
            lambda target=panel_id: self._emit_action(f"panel:{target}"),
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

    def _emit_action(self, action_id: str) -> None:
        """Emit a presentation action identifier for controller routing."""

        self.actionTriggered.emit(action_id)

    def _emit_tool(self, tool_name: str) -> None:
        """Emit a tool selection identifier for controller routing."""

        self.toolSelected.emit(tool_name)

    def _apply_style(self) -> None:
        """Apply the dark professional ribbon theme."""

        self.setStyleSheet(
            """
            QWidget#Ribbon {
                background-color: #11161d;
                border-bottom: 1px solid #262d36;
            }

            QFrame#RibbonTitleBar {
                background-color: #0f1319;
                border-bottom: 1px solid #252b34;
            }

            QLabel#RibbonProductTitle {
                color: #f3f6fb;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QLabel#RibbonProductContext {
                color: #7f8a99;
                font-size: 11px;
                font-weight: 600;
                padding-left: 8px;
            }

            QPushButton#QuickAccessButton {
                background-color: #181e27;
                border: 1px solid #303846;
                border-radius: 4px;
                color: #dce3ed;
                font-size: 11px;
                font-weight: 650;
                min-height: 24px;
                padding: 2px 10px;
            }

            QPushButton#QuickAccessButton:hover {
                background-color: #222b37;
                border-color: #4a8cff;
                color: #ffffff;
            }

            QPushButton#QuickAccessButton:pressed {
                background-color: #2b63c7;
                border-color: #7db4ff;
            }

            QTabWidget#RibbonTabs::pane {
                background-color: #151a22;
                border: none;
                border-top: 1px solid #252b34;
            }

            QTabBar::tab {
                background-color: #121720;
                color: #a8b2c0;
                padding: 5px 16px;
                margin: 0;
                border: none;
                min-height: 22px;
                font-size: 12px;
                font-weight: 600;
            }

            QTabBar::tab:selected {
                background-color: #202834;
                color: #ffffff;
                border-bottom: 2px solid #4a8cff;
            }

            QTabBar::tab:hover {
                background-color: #273140;
                color: #ffffff;
            }

            QScrollArea#RibbonScrollArea {
                background-color: transparent;
                border: none;
            }

            QFrame#RibbonGroup {
                background-color: #1a2029;
                border: 1px solid #2d3542;
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
                color: #dce3ed;
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
