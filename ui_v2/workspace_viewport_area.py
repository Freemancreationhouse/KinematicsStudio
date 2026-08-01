from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui_v2.viewport_manager import ViewportLayout, ViewportManager, ViewportType


@dataclass(frozen=True)
class ViewportPaneDefinition:
    """Presentation definition for one viewport layout pane."""

    viewport_id: str
    title: str
    viewport_type: ViewportType
    widget: QWidget


class SharedSceneViewportSurface(QWidget):
    """Lightweight auxiliary viewport surface that observes the shared scene."""

    def __init__(self, app, mode: str, parent: QWidget | None = None) -> None:
        """Create a surface that uses the existing application render pipeline."""

        super().__init__(parent)

        self._app = app
        self._mode = mode
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event) -> None:
        """Render the shared scene with existing renderer entry points."""

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1A1B1E"))
        if self._mode == "2d" and hasattr(self._app, "render"):
            self._app.render(painter, self.width(), self.height())
        elif self._mode == "3d" and hasattr(self._app, "render3d"):
            self._app.render3d(painter, self.width(), self.height())
        painter.end()


class ViewportPane(QFrame):
    """Titled viewport pane used by the professional layout manager."""

    activated = Signal(str)
    titleDoubleClicked = Signal(str)
    closeRequested = Signal(str)
    splitRequested = Signal(str)

    def __init__(
        self,
        definition: ViewportPaneDefinition,
        parent: QWidget | None = None,
    ) -> None:
        """Create one focused, titled viewport pane."""

        super().__init__(parent)

        self.definition = definition
        self.setObjectName("ViewportPane")
        self.setProperty("active", False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        title_bar = QFrame(self)
        title_bar.setObjectName("ViewportPaneTitleBar")
        title_bar.mouseDoubleClickEvent = self._title_double_click
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 4, 6, 4)
        title_layout.setSpacing(4)

        self._title = QLabel(definition.title, title_bar)
        self._title.setObjectName("ViewportPaneTitle")
        title_layout.addWidget(self._title)
        title_layout.addStretch(1)
        title_layout.addWidget(self._button("Split", self._emit_split, title_bar))
        title_layout.addWidget(self._button("Close", self._emit_close, title_bar))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_bar)
        layout.addWidget(definition.widget, 1)

    def set_active(self, active: bool) -> None:
        """Set active visual state for this pane."""

        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event) -> None:
        """Activate this pane when clicked."""

        self.activated.emit(self.definition.viewport_id)
        super().mousePressEvent(event)

    def _button(
        self,
        text: str,
        callback,
        parent: QWidget,
    ) -> QPushButton:
        """Create a compact pane title action."""

        button = QPushButton(text, parent)
        button.setObjectName("ViewportPaneTitleButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        return button

    def _emit_close(self) -> None:
        """Request this pane be closed from the layout."""

        self.closeRequested.emit(self.definition.viewport_id)

    def _emit_split(self) -> None:
        """Request this pane be split from the layout."""

        self.splitRequested.emit(self.definition.viewport_id)

    def _title_double_click(self, event) -> None:
        """Toggle maximize/restore from the pane title bar."""

        self.titleDoubleClicked.emit(self.definition.viewport_id)
        event.accept()


class ViewportLayoutManager:
    """Professional splitter-based viewport layout coordinator."""

    def __init__(
        self,
        *,
        owner: "WorkspaceViewportArea",
        stack: QStackedWidget,
        viewport_manager: ViewportManager,
    ) -> None:
        """Create a layout manager for the workspace viewport area."""

        self._owner = owner
        self._stack = stack
        self._viewport_manager = viewport_manager
        self._settings = QSettings("Freeman Creations House", "Kinematics Studio")
        self._pane_definitions: dict[str, ViewportPaneDefinition] = {}
        self._open_pane_ids: list[str] = []
        self._previous_open_pane_ids: list[str] = []
        self._active_pane_id = "viewport_2d"
        self._maximized_pane_id: str | None = None
        self._layout = ViewportLayout.SINGLE
        self._current_root: QWidget | None = None

    def register_pane(self, definition: ViewportPaneDefinition) -> None:
        """Register a pane definition available to layouts."""

        self._pane_definitions[definition.viewport_id] = definition

    def initialize(self) -> None:
        """Restore persisted state or fall back to the single viewport layout."""

        if not self.restore_layout_state():
            self.apply_layout(ViewportLayout.SINGLE)

    def apply_layout(self, layout: ViewportLayout | str) -> None:
        """Apply a built-in viewport layout using splitter composition."""

        normalized = self._normalize_layout(layout)
        self._layout = normalized
        self._maximized_pane_id = None
        self._open_pane_ids = list(self._default_panes(normalized))
        if self._active_pane_id not in self._open_pane_ids:
            self._active_pane_id = self._open_pane_ids[0]
        self._viewport_manager.set_layout(normalized)
        self._rearrange()
        self.persist_layout_state()

    def maximize_active_viewport(self) -> None:
        """Maximize the active viewport while remembering the prior layout."""

        self.maximize_viewport(self._active_pane_id)

    def maximize_viewport(self, viewport_id: str) -> None:
        """Maximize one viewport pane."""

        if viewport_id not in self._pane_definitions:
            return
        if self._maximized_pane_id == viewport_id:
            self.restore_previous_layout()
            return
        self._previous_open_pane_ids = list(self._open_pane_ids)
        self._maximized_pane_id = viewport_id
        self._open_pane_ids = [viewport_id]
        self._active_pane_id = viewport_id
        self._rearrange()
        self.persist_layout_state()

    def restore_previous_layout(self) -> None:
        """Restore the layout shown before viewport maximization."""

        if self._previous_open_pane_ids:
            self._open_pane_ids = list(self._previous_open_pane_ids)
        else:
            self._open_pane_ids = list(self._default_panes(self._layout))
        self._maximized_pane_id = None
        if self._active_pane_id not in self._open_pane_ids:
            self._active_pane_id = self._open_pane_ids[0]
        self._rearrange()
        self.persist_layout_state()

    def split_viewport(self, viewport_id: str | None = None) -> None:
        """Split the current layout by reopening the next available viewport."""

        source_id = viewport_id or self._active_pane_id
        if source_id in self._pane_definitions:
            self._active_pane_id = source_id
        for pane_id in self._ordered_available_panes():
            if pane_id not in self._open_pane_ids:
                self._open_pane_ids.append(pane_id)
                break
        self._layout = self._layout_for_count(len(self._open_pane_ids))
        self._viewport_manager.set_layout(self._layout)
        self._rearrange()
        self.persist_layout_state()

    def close_viewport(self, viewport_id: str) -> None:
        """Close one pane while keeping at least one viewport open."""

        if viewport_id not in self._open_pane_ids or len(self._open_pane_ids) == 1:
            return
        self._open_pane_ids.remove(viewport_id)
        if self._active_pane_id == viewport_id:
            self._active_pane_id = self._open_pane_ids[0]
        self._layout = self._layout_for_count(len(self._open_pane_ids))
        self._viewport_manager.set_layout(self._layout)
        self._rearrange()
        self.persist_layout_state()

    def reopen_viewport(self, viewport_id: str) -> None:
        """Reopen a registered pane inside the current layout."""

        if viewport_id not in self._pane_definitions:
            return
        if viewport_id not in self._open_pane_ids:
            self._open_pane_ids.append(viewport_id)
        self._layout = self._layout_for_count(len(self._open_pane_ids))
        self._viewport_manager.set_layout(self._layout)
        self._rearrange()
        self.persist_layout_state()

    def swap_viewport_positions(self, first_id: str, second_id: str) -> None:
        """Swap two visible viewport pane positions."""

        if first_id not in self._open_pane_ids or second_id not in self._open_pane_ids:
            return
        first_index = self._open_pane_ids.index(first_id)
        second_index = self._open_pane_ids.index(second_id)
        self._open_pane_ids[first_index], self._open_pane_ids[second_index] = (
            self._open_pane_ids[second_index],
            self._open_pane_ids[first_index],
        )
        self._rearrange()
        self.persist_layout_state()

    def set_active_viewport(self, viewport_id: str) -> None:
        """Set and highlight the active viewport pane."""

        if viewport_id not in self._pane_definitions:
            return
        self._active_pane_id = viewport_id
        self._viewport_manager.set_active_viewport(viewport_id)
        for pane in self._stack.findChildren(ViewportPane):
            pane.set_active(pane.definition.viewport_id == viewport_id)

    def persist_layout_state(self) -> None:
        """Persist the current viewport layout state."""

        self._settings.setValue("viewport_layout/layout", self._layout.value)
        self._settings.setValue("viewport_layout/open_panes", self._open_pane_ids)
        self._settings.setValue("viewport_layout/active", self._active_pane_id)
        self._settings.setValue("viewport_layout/maximized", self._maximized_pane_id or "")

    def restore_layout_state(self) -> bool:
        """Restore persisted viewport layout state."""

        layout_name = self._settings.value("viewport_layout/layout")
        open_panes = self._settings.value("viewport_layout/open_panes")
        active = self._settings.value("viewport_layout/active")
        maximized = self._settings.value("viewport_layout/maximized")
        if not layout_name:
            return False

        try:
            self._layout = self._normalize_layout(str(layout_name))
        except ValueError:
            return False

        pane_ids = self._coerce_pane_ids(open_panes)
        self._open_pane_ids = [
            pane_id for pane_id in pane_ids if pane_id in self._pane_definitions
        ] or list(self._default_panes(self._layout))
        if active in self._pane_definitions:
            self._active_pane_id = str(active)
        else:
            self._active_pane_id = self._open_pane_ids[0]
        self._maximized_pane_id = (
            str(maximized)
            if maximized and str(maximized) in self._pane_definitions
            else None
        )
        if self._maximized_pane_id:
            self._previous_open_pane_ids = list(self._open_pane_ids)
            self._open_pane_ids = [self._maximized_pane_id]
        self._viewport_manager.set_layout(self._layout)
        self._rearrange()
        return True

    def current_layout(self) -> ViewportLayout:
        """Return the current layout mode."""

        return self._layout

    def _rearrange(self) -> None:
        """Rebuild the splitter layout from current pane ids."""

        previous_root = self._current_root
        root = self._build_layout(self._open_pane_ids)
        self._stack.addWidget(root)
        self._stack.setCurrentWidget(root)
        self._current_root = root
        if previous_root is not None:
            self._stack.removeWidget(previous_root)
            previous_root.setParent(None)
            previous_root.deleteLater()
        self.set_active_viewport(self._active_pane_id)

    def _build_layout(self, pane_ids: list[str]) -> QWidget:
        """Create a QWidget hierarchy for the requested pane ids."""

        if len(pane_ids) == 1:
            return self._pane(pane_ids[0])
        if len(pane_ids) == 2:
            orientation = (
                Qt.Orientation.Vertical
                if self._layout == ViewportLayout.DUAL_VERTICAL
                else Qt.Orientation.Horizontal
            )
            splitter = self._splitter(orientation)
            for pane_id in pane_ids:
                splitter.addWidget(self._pane(pane_id))
            splitter.setSizes([1, 1])
            return splitter
        if len(pane_ids) == 3:
            splitter = self._splitter(Qt.Orientation.Horizontal)
            left = self._splitter(Qt.Orientation.Vertical)
            left.addWidget(self._pane(pane_ids[0]))
            left.addWidget(self._pane(pane_ids[1]))
            left.setSizes([1, 1])
            splitter.addWidget(left)
            splitter.addWidget(self._pane(pane_ids[2]))
            splitter.setSizes([1, 1])
            return splitter

        splitter = self._splitter(Qt.Orientation.Horizontal)
        left = self._splitter(Qt.Orientation.Vertical)
        right = self._splitter(Qt.Orientation.Vertical)
        for pane_id in pane_ids[:2]:
            left.addWidget(self._pane(pane_id))
        for pane_id in pane_ids[2:4]:
            right.addWidget(self._pane(pane_id))
        left.setSizes([1, 1])
        right.setSizes([1, 1])
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([1, 1])
        return splitter

    def _pane(self, viewport_id: str) -> ViewportPane:
        """Create a titled pane from a registered definition."""

        definition = self._pane_definitions[viewport_id]
        pane = ViewportPane(definition, self._owner)
        pane.activated.connect(self.set_active_viewport)
        pane.titleDoubleClicked.connect(self.maximize_viewport)
        pane.closeRequested.connect(self.close_viewport)
        pane.splitRequested.connect(self.split_viewport)
        return pane

    def _splitter(self, orientation: Qt.Orientation) -> QSplitter:
        """Create a professional splitter for viewport layouts."""

        splitter = QSplitter(orientation, self._owner)
        splitter.setObjectName("ViewportLayoutSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)
        return splitter

    def _default_panes(self, layout: ViewportLayout) -> tuple[str, ...]:
        """Return default pane ids for a built-in layout."""

        if layout == ViewportLayout.SINGLE:
            return (self._active_pane_id,)
        if layout in {ViewportLayout.DUAL_HORIZONTAL, ViewportLayout.DUAL_VERTICAL}:
            return ("viewport_2d", "viewport_3d")
        if layout == ViewportLayout.TRIPLE:
            return ("viewport_2d", "viewport_front", "viewport_3d")
        if layout == ViewportLayout.QUAD:
            return (
                "viewport_2d",
                "viewport_front",
                "viewport_right",
                "viewport_3d",
            )
        return tuple(self._open_pane_ids or ("viewport_2d",))

    def _ordered_available_panes(self) -> tuple[str, ...]:
        """Return the preferred order for reopening/splitting panes."""

        return (
            "viewport_2d",
            "viewport_front",
            "viewport_right",
            "viewport_3d",
            "viewport_user",
            "viewport_camera",
            "viewport_section",
        )

    def _layout_for_count(self, count_value: int) -> ViewportLayout:
        """Return a built-in layout matching a visible pane count."""

        if count_value <= 1:
            return ViewportLayout.SINGLE
        if count_value == 2:
            return ViewportLayout.DUAL_HORIZONTAL
        if count_value == 3:
            return ViewportLayout.TRIPLE
        return ViewportLayout.QUAD

    def _normalize_layout(self, layout: ViewportLayout | str) -> ViewportLayout:
        """Normalize a layout enum or display string."""

        if isinstance(layout, ViewportLayout):
            return layout
        for item in ViewportLayout:
            if item.value.lower() == str(layout).lower():
                return item
        raise ValueError(f"Unsupported viewport layout: {layout}")

    def _coerce_pane_ids(self, value) -> tuple[str, ...]:
        """Convert QSettings pane id values into a stable tuple."""

        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, (list, tuple)):
            return tuple(str(item) for item in value if str(item))
        return ()


class WorkspaceViewportArea(QWidget):
    """Reusable container for professional single and multi-viewport layouts."""

    active_view_changed = Signal(str)

    def __init__(
        self,
        canvas: QWidget,
        viewport3d: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        """Create a viewport area from externally owned viewport dependencies."""

        super().__init__(parent)

        self._canvas = canvas
        self._viewport3d = viewport3d
        self._stack = QStackedWidget(self)
        self._active_view_name = "2d"
        self._viewport_manager = ViewportManager(
            workspace_provider=getattr(canvas, "app", None),
            parent=self,
        )
        self._layout_manager = ViewportLayoutManager(
            owner=self,
            stack=self._stack,
            viewport_manager=self._viewport_manager,
        )

        self._register_initial_viewports()
        self._layout_manager.initialize()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._stack)
        self._apply_style()

    def show_2d(self) -> None:
        """Make the 2D canvas the active viewport."""

        self._layout_manager.set_active_viewport("viewport_2d")
        self._layout_manager.apply_layout(ViewportLayout.SINGLE)
        self._active_view_name = "2d"
        self.active_view_changed.emit("2d")

    def show_3d(self) -> None:
        """Make the 3D viewport the active viewport."""

        self._layout_manager.set_active_viewport("viewport_3d")
        self._layout_manager.apply_layout(ViewportLayout.SINGLE)
        self._active_view_name = "3d"
        self.active_view_changed.emit("3d")

    def toggle_view(self) -> None:
        """Toggle between the 2D canvas and the 3D viewport."""

        if self._active_view_name == "2d":
            self.show_3d()
        else:
            self.show_2d()

    def active_view(self) -> QWidget:
        """Return the currently active viewport widget."""

        active = self._viewport_manager.active_viewport()
        if active is not None:
            return active.widget
        return self._canvas

    def canvas(self) -> QWidget:
        """Return the injected 2D canvas widget."""

        return self._canvas

    def viewport3d(self) -> QWidget:
        """Return the injected 3D viewport widget."""

        return self._viewport3d

    def viewport_manager(self) -> ViewportManager:
        """Return the viewport framework manager."""

        return self._viewport_manager

    def viewport_layout_manager(self) -> ViewportLayoutManager:
        """Return the professional viewport layout manager."""

        return self._layout_manager

    def active_viewport_id(self) -> str | None:
        """Return the active viewport id from the manager."""

        return self._viewport_manager.active_viewport_id()

    def set_layout(self, layout: ViewportLayout | str) -> None:
        """Apply a professional viewport layout."""

        self._layout_manager.apply_layout(layout)

    def single_view(self) -> None:
        """Apply the single viewport layout."""

        self.set_layout(ViewportLayout.SINGLE)

    def dual_horizontal(self) -> None:
        """Apply the dual horizontal viewport layout."""

        self.set_layout(ViewportLayout.DUAL_HORIZONTAL)

    def dual_vertical(self) -> None:
        """Apply the dual vertical viewport layout."""

        self.set_layout(ViewportLayout.DUAL_VERTICAL)

    def triple_view(self) -> None:
        """Apply the triple viewport layout."""

        self.set_layout(ViewportLayout.TRIPLE)

    def quad_view(self) -> None:
        """Apply the quad viewport layout."""

        self.set_layout(ViewportLayout.QUAD)

    def maximize_active_viewport(self) -> None:
        """Maximize the active viewport."""

        self._layout_manager.maximize_active_viewport()

    def restore_previous_layout(self) -> None:
        """Restore the previous viewport layout."""

        self._layout_manager.restore_previous_layout()

    def split_viewport(self) -> None:
        """Split the active viewport layout."""

        self._layout_manager.split_viewport()

    def close_active_viewport(self) -> None:
        """Close the active viewport pane."""

        active_id = self.active_viewport_id()
        if active_id is not None:
            self._layout_manager.close_viewport(active_id)

    def reopen_viewport(self, viewport_id: str) -> None:
        """Reopen a registered viewport pane."""

        self._layout_manager.reopen_viewport(viewport_id)

    def swap_viewport_positions(self, first_id: str, second_id: str) -> None:
        """Swap two viewport pane positions."""

        self._layout_manager.swap_viewport_positions(first_id, second_id)

    def _register_initial_viewports(self) -> None:
        """Register the existing and auxiliary shared-scene viewport panes."""

        app = getattr(self._canvas, "app", None)
        engine = getattr(app, "engine", None)
        panes = (
            ViewportPaneDefinition(
                "viewport_2d",
                "Top",
                ViewportType.TOP,
                self._canvas,
            ),
            ViewportPaneDefinition(
                "viewport_front",
                "Front",
                ViewportType.FRONT,
                SharedSceneViewportSurface(app, "3d", self),
            ),
            ViewportPaneDefinition(
                "viewport_right",
                "Right",
                ViewportType.RIGHT,
                SharedSceneViewportSurface(app, "3d", self),
            ),
            ViewportPaneDefinition(
                "viewport_3d",
                "Perspective",
                ViewportType.PERSPECTIVE,
                self._viewport3d,
            ),
            ViewportPaneDefinition(
                "viewport_user",
                "User",
                ViewportType.USER,
                SharedSceneViewportSurface(app, "3d", self),
            ),
            ViewportPaneDefinition(
                "viewport_camera",
                "Camera",
                ViewportType.CAMERA,
                SharedSceneViewportSurface(app, "3d", self),
            ),
            ViewportPaneDefinition(
                "viewport_section",
                "Section",
                ViewportType.SECTION,
                SharedSceneViewportSurface(app, "3d", self),
            ),
        )

        for pane in panes:
            self._layout_manager.register_pane(pane)
            self._viewport_manager.register_viewport(
                viewport_id=pane.viewport_id,
                viewport_type=pane.viewport_type,
                widget=pane.widget,
                camera=self._camera_for(pane.viewport_type),
                renderer=getattr(engine, "renderer3d", None)
                if pane.viewport_type != ViewportType.TOP
                else getattr(engine, "renderer", None),
                overlay_manager=None,
                toolbar=None,
                dock_container=self,
            )
        self._viewport_manager.set_layout(ViewportLayout.SINGLE)
        self._viewport_manager.set_active_viewport("viewport_2d")

    def _camera_for(self, viewport_type: ViewportType):
        """Return the existing camera object for a viewport type."""

        app = getattr(self._canvas, "app", None)
        if viewport_type == ViewportType.TOP:
            return getattr(self._canvas, "camera", None)
        return getattr(app, "camera3d", None)

    def _apply_style(self) -> None:
        """Apply professional viewport layout styling."""

        self.setStyleSheet(
            """
            QStackedWidget {
                background-color: #1A1B1E;
                border: none;
            }

            QSplitter#ViewportLayoutSplitter {
                background-color: #1A1B1E;
            }

            QSplitter#ViewportLayoutSplitter::handle {
                background-color: #383B42;
            }

            QSplitter#ViewportLayoutSplitter::handle:hover {
                background-color: #4FA3FF;
            }

            QFrame#ViewportPane {
                background-color: #1A1B1E;
                border: 1px solid #383B42;
                border-radius: 8px;
            }

            QFrame#ViewportPane[active="true"] {
                border-color: #4FA3FF;
            }

            QFrame#ViewportPaneTitleBar {
                background-color: #25272C;
                border-bottom: 1px solid #383B42;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }

            QLabel#ViewportPaneTitle {
                color: #F0F3F7;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton#ViewportPaneTitleButton {
                background-color: #30333A;
                border: 1px solid #454952;
                border-radius: 6px;
                color: #C8CED8;
                font-size: 10px;
                min-height: 20px;
                padding: 1px 8px;
            }

            QPushButton#ViewportPaneTitleButton:hover {
                background-color: #3D4148;
                border-color: #4FA3FF;
                color: #FFFFFF;
            }
            """
        )
