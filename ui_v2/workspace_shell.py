from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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
        self._view_title = QLabel("Perspective", self)
        self._view_title.setObjectName("ViewportTitle")
        self._view_subtitle = QLabel("User View", self)
        self._view_subtitle.setObjectName("ViewportSubtitle")
        self._selection_indicator = QLabel("Selection: Object", self)
        self._snap_indicator = QLabel("Snap: OFF", self)
        self._grid_indicator = self._toggle_button("Grid: ON", self)
        self._axis_indicator = self._toggle_button("Axis: ON", self)
        self._units_indicator = QLabel("Units: mm", self)
        self._origin_indicator = QLabel("Origin: 0, 0, 0", self)
        self._target_indicator = QLabel("Target: 0, 0, 0", self)
        self._coordinate_indicator = QLabel("X 0.00  Y 0.00  Z 0.00", self)
        self._view_mode_selector = QComboBox(self)
        self._view_mode_selector.setObjectName("ViewportModeSelector")
        self._view_mode_selector.addItems(
            ("Wireframe", "Hidden Line", "Shaded", "Rendered", "X-Ray")
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._create_title_bar())
        layout.addWidget(self._viewport_area, 1)
        layout.addWidget(self._create_overlay_bar())

    def viewport_area(self) -> QWidget:
        """Return the hosted viewport area widget."""

        return self._viewport_area

    def set_view_title(self, title: str, subtitle: str = "") -> None:
        """Update the visible viewport view title."""

        self._view_title.setText(title)
        self._view_subtitle.setText(subtitle)
        self._view_subtitle.setVisible(bool(subtitle))

    def set_selection_mode(self, mode: str) -> None:
        """Update the viewport selection mode indicator."""

        self._selection_indicator.setText(f"Selection: {mode}")

    def set_snap_state(self, enabled: bool) -> None:
        """Update the viewport snap indicator."""

        self._snap_indicator.setText(f"Snap: {'ON' if enabled else 'OFF'}")

    def set_grid_state(self, enabled: bool) -> None:
        """Update the viewport grid indicator."""

        self._grid_indicator.setText(f"Grid: {'ON' if enabled else 'OFF'}")
        self._grid_indicator.setChecked(enabled)

    def set_axis_state(self, enabled: bool) -> None:
        """Update the viewport axis indicator."""

        self._axis_indicator.setText(f"Axis: {'ON' if enabled else 'OFF'}")
        self._axis_indicator.setChecked(enabled)

    def set_units(self, units: str) -> None:
        """Update the viewport units indicator."""

        self._units_indicator.setText(f"Units: {units}")

    def set_camera_target(self, target: str) -> None:
        """Update the viewport camera target indicator."""

        self._target_indicator.setText(f"Target: {target}")

    def set_coordinates(self, coordinates: str) -> None:
        """Update the viewport coordinate display."""

        self._coordinate_indicator.setText(coordinates)

    def set_view_mode(self, mode: str) -> None:
        """Update the visible view mode selector without changing rendering."""

        index = self._view_mode_selector.findText(mode)
        if index >= 0:
            self._view_mode_selector.setCurrentIndex(index)

    def _create_title_bar(self) -> QFrame:
        """Create the compact professional viewport title and controls."""

        title_bar = QFrame(self)
        title_bar.setObjectName("ViewportTitleBar")

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 6, 12, 6)
        title_layout.setSpacing(8)

        title_group = QFrame(title_bar)
        title_group.setObjectName("ViewportTitleGroup")
        title_group_layout = QVBoxLayout(title_group)
        title_group_layout.setContentsMargins(0, 0, 0, 0)
        title_group_layout.setSpacing(0)
        title_group_layout.addWidget(self._view_title)
        title_group_layout.addWidget(self._view_subtitle)

        title_layout.addWidget(title_group)
        title_layout.addWidget(self._create_view_strip(title_bar))
        title_layout.addStretch(1)
        title_layout.addWidget(self._view_mode_selector)
        title_layout.addWidget(self._create_navigation_toolbar(title_bar))

        return title_bar

    def _create_view_strip(self, parent: QWidget) -> QFrame:
        """Create non-invasive viewport orientation labels."""

        strip = QFrame(parent)
        strip.setObjectName("ViewportViewStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for text in ("Top", "Front", "Right", "User View"):
            layout.addWidget(self._chip(text, strip, "ViewportViewChip"))

        return strip

    def _create_navigation_toolbar(self, parent: QWidget) -> QFrame:
        """Create the viewport navigation toolbar using existing action ids."""

        toolbar = QFrame(parent)
        toolbar.setObjectName("ViewportNavigationToolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for text, action_id in (
            ("2D", "view_2d"),
            ("3D", "view_3d"),
            ("Home", "view:home"),
            ("Extents", "view:zoom_extents"),
            ("Selected", "view:zoom_selected"),
        ):
            layout.addWidget(self._action_button(text, action_id, toolbar))

        return toolbar

    def _create_overlay_bar(self) -> QFrame:
        """Create the lower viewport overlay indicators."""

        overlay = QFrame(self)
        overlay.setObjectName("ViewportOverlayBar")
        layout = QHBoxLayout(overlay)
        layout.setContentsMargins(12, 5, 12, 5)
        layout.setSpacing(6)

        for indicator in (
            self._selection_indicator,
            self._snap_indicator,
            self._units_indicator,
            self._origin_indicator,
            self._target_indicator,
        ):
            indicator.setObjectName("ViewportStatusChip")
            layout.addWidget(indicator)

        self._grid_indicator.setObjectName("ViewportToggleChip")
        self._axis_indicator.setObjectName("ViewportToggleChip")
        layout.addWidget(self._grid_indicator)
        layout.addWidget(self._axis_indicator)
        layout.addStretch(1)
        self._coordinate_indicator.setObjectName("ViewportCoordinateDisplay")
        layout.addWidget(self._coordinate_indicator)

        return overlay

    def _action_button(
        self,
        text: str,
        action_id: str,
        parent: QWidget,
    ) -> QPushButton:
        """Create a compact viewport chrome action button."""

        button = QPushButton(text, parent)
        button.setObjectName("ViewportControlButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(
            lambda checked=False, current=action_id: (
                self.actionTriggered.emit(current)
            )
        )
        return button

    def _toggle_button(self, text: str, parent: QWidget) -> QPushButton:
        """Create a presentation-only viewport state toggle."""

        button = QPushButton(text, parent)
        button.setCheckable(True)
        button.setChecked(True)
        button.setCursor(Qt.PointingHandCursor)
        button.toggled.connect(
            lambda checked, current=button, label=text.split(":", 1)[0]: (
                current.setText(f"{label}: {'ON' if checked else 'OFF'}")
            )
        )
        return button

    def _chip(
        self,
        text: str,
        parent: QWidget,
        object_name: str,
    ) -> QLabel:
        """Create a compact viewport information chip."""

        chip = QLabel(text, parent)
        chip.setObjectName(object_name)
        chip.setAlignment(Qt.AlignCenter)
        return chip


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
                background-color: #1e1f22;
            }

            QWidget#WorkspaceShellBody {
                background-color: #1e1f22;
            }

            QFrame#PropertiesSidebar {
                background-color: #2b2d31;
                border-left: 1px solid #383b42;
            }

            QFrame#WorkspaceDockRail {
                background-color: #26282d;
                border-left: 1px solid #383b42;
                border-right: 1px solid #383b42;
            }

            QLabel#WorkspaceDockRailTitle {
                color: #8f98a6;
                font-size: 8px;
                font-weight: 800;
                letter-spacing: 1px;
            }

            QPushButton#WorkspaceDockRailButton {
                background-color: #30333a;
                border: 1px solid #454952;
                border-radius: 6px;
                color: #d6dbe3;
                font-size: 9px;
                font-weight: 700;
            }

            QPushButton#WorkspaceDockRailButton:hover {
                background-color: #3d4148;
                border-color: #4fa3ff;
                color: #ffffff;
            }

            QFrame#WorkspaceViewportFrame {
                background-color: #1a1b1e;
                border-left: 1px solid #383b42;
                border-right: 1px solid #383b42;
            }

            QFrame#ViewportTitleBar {
                background-color: #25272c;
                border-bottom: 1px solid #383b42;
            }

            QFrame#ViewportTitleGroup {
                background-color: transparent;
            }

            QLabel#ViewportTitle {
                color: #f0f3f7;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#ViewportSubtitle {
                color: #8f98a6;
                font-size: 9px;
                font-weight: 500;
            }

            QFrame#ViewportViewStrip,
            QFrame#ViewportNavigationToolbar {
                background-color: transparent;
            }

            QLabel#ViewportViewChip,
            QLabel#ViewportStatusChip,
            QLabel#ViewportCoordinateDisplay,
            QPushButton#ViewportToggleChip {
                background-color: #30333a;
                border: 1px solid #454952;
                border-radius: 6px;
                color: #c8ced8;
                font-size: 10px;
                min-height: 20px;
                padding: 1px 8px;
            }

            QPushButton#ViewportToggleChip:checked {
                border-color: #4fa3ff;
                color: #f0f3f7;
            }

            QPushButton#ViewportToggleChip:hover {
                background-color: #3d4148;
                border-color: #4fa3ff;
            }

            QLabel#ViewportViewChip {
                color: #9fa7b3;
                padding-left: 7px;
                padding-right: 7px;
            }

            QLabel#ViewportCoordinateDisplay {
                color: #f0f3f7;
                font-weight: 650;
            }

            QComboBox#ViewportModeSelector {
                background-color: #30333a;
                border: 1px solid #454952;
                border-radius: 6px;
                color: #f0f3f7;
                font-size: 10px;
                min-height: 22px;
                padding-left: 8px;
                padding-right: 8px;
            }

            QComboBox#ViewportModeSelector:hover {
                background-color: #3d4148;
                border-color: #4fa3ff;
            }

            QComboBox#ViewportModeSelector::drop-down {
                border: none;
                width: 18px;
            }

            QComboBox#ViewportModeSelector QAbstractItemView {
                background-color: #2b2d31;
                border: 1px solid #454952;
                color: #f0f3f7;
                selection-background-color: #3d4148;
                selection-color: #ffffff;
            }

            QPushButton#ViewportControlButton {
                background-color: #30333a;
                border: 1px solid #454952;
                border-radius: 6px;
                color: #d6dbe3;
                font-size: 10px;
                font-weight: 650;
                min-height: 22px;
                padding: 1px 8px;
            }

            QPushButton#ViewportControlButton:hover {
                background-color: #3d4148;
                border-color: #4fa3ff;
                color: #ffffff;
            }

            QFrame#ViewportOverlayBar {
                background-color: #25272c;
                border-top: 1px solid #383b42;
            }
            """
        )
