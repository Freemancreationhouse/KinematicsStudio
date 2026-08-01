from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class RibbonHost(QWidget):
    """Top shell region that hosts the injected ribbon widget."""

    def __init__(self, ribbon: QWidget, parent: QWidget | None = None):
        """Create a ribbon host from an externally supplied ribbon widget."""

        super().__init__(parent)

        self._ribbon = ribbon
        self.setObjectName("RibbonHost")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._ribbon)

    def ribbon(self) -> QWidget:
        """Return the hosted ribbon widget."""

        return self._ribbon


class PropertiesSidebar(QFrame):
    """Right shell region that hosts the injected property panel widget."""

    INITIAL_WIDTH = 300
    MINIMUM_WIDTH = 260
    MAXIMUM_WIDTH = 420

    def __init__(self, property_panel: QWidget, parent: QWidget | None = None):
        """Create a properties sidebar from an externally supplied panel."""

        super().__init__(parent)

        self._property_panel = property_panel
        self.setObjectName("PropertiesSidebar")
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setMaximumWidth(self.MAXIMUM_WIDTH)
        self.resize(self.INITIAL_WIDTH, self.height())
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._property_panel)

    def property_panel(self) -> QWidget:
        """Return the hosted property panel widget."""

        return self._property_panel


class CommandLineHost(QWidget):
    """Bottom shell region that hosts the injected command bar widget."""

    def __init__(self, command_bar: QWidget, parent: QWidget | None = None):
        """Create a command-line host from an externally supplied command bar."""

        super().__init__(parent)

        self._command_bar = command_bar
        self.setObjectName("CommandLineHost")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._command_bar)

    def command_bar(self) -> QWidget:
        """Return the hosted command bar widget."""

        return self._command_bar


class StatusBarHost(QWidget):
    """Bottom shell region that hosts the injected status bar widget."""

    def __init__(self, status_bar: QWidget, parent: QWidget | None = None):
        """Create a status-bar host from an externally supplied status bar."""

        super().__init__(parent)

        self._status_bar = status_bar
        self.setObjectName("StatusBarHost")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._status_bar)

    def status_bar(self) -> QWidget:
        """Return the hosted status bar widget."""

        return self._status_bar


class WorkspaceDockRail(QFrame):
    """Collapsed professional dock rail for lazy workspace panel access."""

    actionTriggered = Signal(str)

    def __init__(
        self,
        title: str,
        actions: tuple[tuple[str, str], ...],
        parent: QWidget | None = None,
    ):
        """Create a collapsed rail that emits existing panel action ids."""

        super().__init__(parent)

        self.setObjectName("WorkspaceDockRail")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(48)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 8, 5, 8)
        layout.setSpacing(6)

        label = QLabel(title, self)
        label.setObjectName("WorkspaceDockRailTitle")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        for text, action_id in actions:
            button = QPushButton(text, self)
            button.setObjectName("WorkspaceDockRailButton")
            button.setCursor(Qt.PointingHandCursor)
            button.setToolTip(text)
            button.setFixedSize(38, 38)
            button.clicked.connect(
                lambda checked=False, current=action_id: (
                    self.actionTriggered.emit(current)
                )
            )
            layout.addWidget(button)

        layout.addStretch(1)


class WorkspaceViewportFrame(QFrame):
    """Professional viewport frame with compact controls around the viewport."""

    actionTriggered = Signal(str)

    def __init__(self, viewport_area: QWidget, parent: QWidget | None = None):
        """Create a viewport-first frame around the injected viewport area."""

        super().__init__(parent)

        self._viewport_area = viewport_area
        self.setObjectName("WorkspaceViewportFrame")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QFrame(self)
        title_bar.setObjectName("ViewportTitleBar")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 4, 8, 4)
        title_layout.setSpacing(6)

        title = QLabel("Model Viewport", title_bar)
        title.setObjectName("ViewportTitle")
        title_layout.addWidget(title)
        title_layout.addStretch(1)

        for text, action_id in (
            ("2D", "view_2d"),
            ("3D", "view_3d"),
            ("Home", "view:home"),
            ("Extents", "view:zoom_extents"),
            ("Selected", "view:zoom_selected"),
        ):
            button = QPushButton(text, title_bar)
            button.setObjectName("ViewportControlButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, current=action_id: (
                    self.actionTriggered.emit(current)
                )
            )
            title_layout.addWidget(button)

        layout.addWidget(title_bar)
        layout.addWidget(self._viewport_area, 1)

    def viewport_area(self) -> QWidget:
        """Return the hosted viewport area widget."""

        return self._viewport_area


class WorkspaceShell(QWidget):
    """Reusable viewport-first application shell composed from injected widgets."""

    actionTriggered = Signal(str)

    def __init__(
        self,
        ribbon: QWidget,
        left_toolbox: QWidget,
        viewport_area: QWidget,
        property_panel: QWidget,
        command_bar: QWidget,
        status_bar: QWidget,
        parent: QWidget | None = None,
    ):
        """Create the shell without instantiating or routing child widgets."""

        super().__init__(parent)

        self._left_toolbox = left_toolbox
        self._viewport_area = viewport_area
        self._viewport_frame = WorkspaceViewportFrame(viewport_area, self)
        self._ribbon_host = RibbonHost(ribbon, self)
        self._properties_sidebar = PropertiesSidebar(property_panel, self)
        self._command_line_host = CommandLineHost(command_bar, self)
        self._status_bar_host = StatusBarHost(status_bar, self)
        self._left_dock = WorkspaceDockRail(
            "PROJECT",
            (
                ("Prj", "panel:explorer"),
                ("Lay", "panel:layer_manager"),
                ("Ast", "panel:project_manager"),
                ("Blk", "panel:block_manager"),
            ),
            self,
        )
        self._right_dock = WorkspaceDockRail(
            "TOOLS",
            (
                ("Prop", "panel:project_manager"),
                ("Insp", "panel:selection_sets"),
                ("AI", "command_palette"),
            ),
            self,
        )

        self.setObjectName("WorkspaceShell")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._connect_internal_actions()
        self._configure_child_sizing()
        self._build_layout()
        self._apply_style()

    def ribbon(self) -> QWidget:
        """Return the shell ribbon widget."""

        return self._ribbon_host.ribbon()

    def left_toolbox(self) -> QWidget:
        """Return the shell left toolbox widget."""

        return self._left_toolbox

    def viewport_area(self) -> QWidget:
        """Return the shell viewport area widget."""

        return self._viewport_area

    def property_panel(self) -> QWidget:
        """Return the shell property panel widget."""

        return self._properties_sidebar.property_panel()

    def command_bar(self) -> QWidget:
        """Return the shell command bar widget."""

        return self._command_line_host.command_bar()

    def status_bar(self) -> QWidget:
        """Return the shell status bar widget."""

        return self._status_bar_host.status_bar()

    def _configure_child_sizing(self) -> None:
        """Configure layout sizing so the viewport naturally dominates."""

        self._left_toolbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._viewport_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._properties_sidebar.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Expanding,
        )

    def _connect_internal_actions(self) -> None:
        """Forward shell chrome actions without routing application logic."""

        self._left_dock.actionTriggered.connect(self.actionTriggered)
        self._right_dock.actionTriggered.connect(self.actionTriggered)
        self._viewport_frame.actionTriggered.connect(self.actionTriggered)

    def _build_layout(self) -> None:
        """Compose the permanent application shell layout."""

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        body = QWidget(self)
        body.setObjectName("WorkspaceShellBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._left_toolbox)
        body_layout.addWidget(self._left_dock)
        body_layout.addWidget(self._viewport_frame, 1)
        body_layout.addWidget(self._properties_sidebar)
        body_layout.addWidget(self._right_dock)

        root_layout.addWidget(self._ribbon_host)
        root_layout.addWidget(body, 1)
        root_layout.addWidget(self._command_line_host)
        root_layout.addWidget(self._status_bar_host)

    def _apply_style(self) -> None:
        """Apply neutral shell styling without affecting child behavior."""

        self.setStyleSheet(
            """
            QWidget#WorkspaceShell {
                background-color: #0e1117;
            }

            QWidget#WorkspaceShellBody {
                background-color: #0e1117;
            }

            QFrame#PropertiesSidebar {
                background-color: #151a22;
                border-left: 1px solid #29313d;
            }

            QFrame#WorkspaceDockRail {
                background-color: #111720;
                border-left: 1px solid #222a35;
                border-right: 1px solid #222a35;
            }

            QLabel#WorkspaceDockRailTitle {
                color: #697586;
                font-size: 8px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QPushButton#WorkspaceDockRailButton {
                background-color: #19212b;
                border: 1px solid #303a49;
                border-radius: 5px;
                color: #c7d0dc;
                font-size: 9px;
                font-weight: 700;
            }

            QPushButton#WorkspaceDockRailButton:hover {
                background-color: #243041;
                border-color: #4a8cff;
                color: #ffffff;
            }

            QFrame#WorkspaceViewportFrame {
                background-color: #0b0e13;
                border-left: 1px solid #1f2630;
                border-right: 1px solid #1f2630;
            }

            QFrame#ViewportTitleBar {
                background-color: #111720;
                border-bottom: 1px solid #29313d;
            }

            QLabel#ViewportTitle {
                color: #dce3ed;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton#ViewportControlButton {
                background-color: #18202a;
                border: 1px solid #303a49;
                border-radius: 4px;
                color: #c7d0dc;
                font-size: 10px;
                font-weight: 650;
                min-height: 20px;
                padding: 1px 8px;
            }

            QPushButton#ViewportControlButton:hover {
                background-color: #243041;
                border-color: #4a8cff;
                color: #ffffff;
            }
            """
        )
