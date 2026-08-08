from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QToolButton, QVBoxLayout, QWidget

from engine.geometry import BoundingBox3D


class NavigationBar(QWidget):
    """Viewport-local navigation toolbar for professional 3D camera control."""

    navigationModeChanged = Signal(str)
    cameraChanged = Signal(str)

    def __init__(
        self,
        *,
        camera: Any,
        controller: Any,
        parent: QWidget | None = None,
        entities_provider: Callable[[], Iterable[Any]] | None = None,
        selection_provider: Callable[[], Iterable[Any]] | None = None,
        update_callback: Callable[[], None] | None = None,
        default_mode: str = "orbit",
    ) -> None:
        """Create a Navigation Bar bound to one viewport camera."""

        super().__init__(parent)

        self._camera = camera
        self._controller = controller
        self._entities_provider = entities_provider
        self._selection_provider = selection_provider
        self._update_callback = update_callback
        self._navigation_mode = (
            default_mode
            if default_mode in {"orbit", "pan"}
            else ""
        )
        self._buttons: dict[str, QToolButton] = {}

        self.setObjectName("KinematicsNavigationBar")
        self.setFixedWidth(46)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._build_ui()
        self._sync_state()

        if parent is not None:
            parent.installEventFilter(self)
        self.reposition()
        self.show()

    def reposition(self) -> None:
        """Place the Navigation Bar along the right side of the viewport."""

        parent = self.parentWidget()
        if parent is None:
            return

        margin = 16
        preferred_y = 202
        available_height = max(120, parent.height() - preferred_y - margin)
        self.setFixedHeight(min(self.sizeHint().height(), available_height))
        self.move(
            max(margin, parent.width() - self.width() - margin),
            min(preferred_y, max(margin, parent.height() - self.height() - margin)),
        )
        self.raise_()

    def set_navigation_mode(self, mode: str) -> None:
        """Set the viewport-local navigation interaction mode."""

        if mode not in {"orbit", "pan"}:
            return

        self._navigation_mode = mode
        self._buttons["orbit"].setChecked(mode == "orbit")
        self._buttons["pan"].setChecked(mode == "pan")
        self.navigationModeChanged.emit(mode)

    def navigation_mode(self) -> str:
        """Return the current viewport-local navigation mode."""

        return self._navigation_mode

    def paintEvent(self, event) -> None:
        """Paint a subtle professional overlay background."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QColor(96, 106, 120, 110))
        painter.setBrush(QColor(21, 24, 29, 188))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        painter.end()
        super().paintEvent(event)

    def eventFilter(self, watched, event) -> bool:
        """Keep the bar anchored while the parent viewport resizes."""

        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.reposition()
        return super().eventFilter(watched, event)

    def _build_ui(self) -> None:
        """Create all Navigation Bar controls."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 7, 5, 7)
        layout.setSpacing(5)

        self._add_button(layout, "home", "HME", "Home View", self._home_view)
        self._add_button(layout, "extents", "EXT", "Zoom Extents", self._zoom_extents)
        self._add_button(layout, "selected", "SEL", "Zoom Selected", self._zoom_selected)
        self._add_separator(layout)
        self._add_button(
            layout,
            "orbit",
            "ORB",
            "Orbit navigation mode",
            lambda: self.set_navigation_mode("orbit"),
            checkable=True,
        )
        self._add_button(
            layout,
            "pan",
            "PAN",
            "Pan navigation mode",
            lambda: self.set_navigation_mode("pan"),
            checkable=True,
        )
        self._add_button(layout, "walk", "WLK", "Walk navigation is not available", None)
        self._add_button(layout, "fly", "FLY", "Fly navigation is not available", None)
        self._buttons["walk"].setEnabled(False)
        self._buttons["fly"].setEnabled(False)
        self._add_separator(layout)
        self._add_button(
            layout,
            "projection",
            "PER",
            "Toggle Perspective / Orthographic projection",
            self._toggle_projection,
            checkable=True,
        )
        self._add_button(
            layout,
            "grid",
            "GRD",
            "Toggle viewport grid",
            self._toggle_grid,
            checkable=True,
        )
        self._add_button(
            layout,
            "axes",
            "AXS",
            "Toggle viewport axes",
            self._toggle_axes,
            checkable=True,
        )
        self._add_button(
            layout,
            "origin",
            "ORG",
            "Toggle world origin marker",
            self._toggle_origin,
            checkable=True,
        )
        self._add_separator(layout)
        self._add_button(layout, "camera", "CAM", "Camera Settings", self._camera_settings)
        self._add_button(layout, "viewport", "VP", "Viewport Settings", self._viewport_settings)
        layout.addStretch(1)

        self.setStyleSheet(
            """
            QWidget#KinematicsNavigationBar {
                background: transparent;
            }
            QToolButton {
                background-color: rgba(37, 43, 51, 210);
                border: 1px solid rgba(101, 113, 130, 135);
                border-radius: 5px;
                color: #DCE5F2;
                font-family: Segoe UI;
                font-size: 7px;
                font-weight: 700;
                min-width: 32px;
                max-width: 32px;
                min-height: 24px;
                max-height: 24px;
                padding: 0;
            }
            QToolButton:hover {
                background-color: rgba(61, 74, 89, 230);
                border-color: #4FA3FF;
                color: #F4F7FA;
            }
            QToolButton:checked {
                background-color: rgba(79, 163, 255, 220);
                border-color: #8DC6FF;
                color: #101820;
            }
            QToolButton:disabled {
                background-color: rgba(30, 34, 40, 150);
                border-color: rgba(70, 78, 90, 90);
                color: #6E7784;
            }
            """
        )

    def _add_button(
        self,
        layout: QVBoxLayout,
        key: str,
        text: str,
        tooltip: str,
        callback: Callable[[], None] | None,
        *,
        checkable: bool = False,
    ) -> None:
        """Add a compact professional navigation button."""

        button = QToolButton(self)
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCheckable(checkable)
        button.setAutoRaise(False)
        if callback is not None:
            button.clicked.connect(lambda _checked=False, slot=callback: slot())
        layout.addWidget(button)
        self._buttons[key] = button

    def _add_separator(self, layout: QVBoxLayout) -> None:
        """Add a compact separator between navigation groups."""

        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(101, 113, 130, 95);")
        layout.addWidget(line)

    def _home_view(self) -> None:
        """Return the active viewport camera to its home state."""

        home = getattr(self._controller, "home_view", None)
        if callable(home):
            home()
        else:
            camera_home = getattr(self._camera, "home_view", None)
            if callable(camera_home):
                camera_home()
        self._camera_updated("Home View")

    def _zoom_extents(self) -> None:
        """Frame all visible shared-scene entities in this viewport camera."""

        fit = getattr(self._controller, "fit_view", None)
        bounds = self._bounds_from(self._entities())
        if callable(fit):
            fit(bounds if bounds.valid else None)
        elif hasattr(self._camera, "fit_bounds"):
            self._camera.fit_bounds(bounds if bounds.valid else None)
        self._camera_updated("Zoom Extents")

    def _zoom_selected(self) -> None:
        """Frame the current shared selection or fall back to all extents."""

        bounds = self._bounds_from(self._selection())
        if not bounds.valid:
            self._zoom_extents()
            return

        fit = getattr(self._controller, "fit_view", None)
        if callable(fit):
            fit(bounds)
        elif hasattr(self._camera, "fit_bounds"):
            self._camera.fit_bounds(bounds)
        self._camera_updated("Zoom Selected")

    def _toggle_projection(self) -> None:
        """Toggle this viewport camera between Perspective and Orthographic."""

        state = self._camera.state
        state.projection_mode = (
            "orthographic"
            if state.projection_mode == "perspective"
            else "perspective"
        )
        self._sync_state()
        self._camera_updated("Projection Toggle")

    def _toggle_grid(self) -> None:
        """Toggle grid visibility for this viewport only."""

        state = self._camera.state
        state.grid_visible = not bool(getattr(state, "grid_visible", True))
        self._sync_state()
        self._camera_updated("Grid Toggle")

    def _toggle_axes(self) -> None:
        """Toggle axis indicator visibility for this viewport only."""

        state = self._camera.state
        state.axis_visible = not bool(getattr(state, "axis_visible", True))
        self._sync_state()
        self._camera_updated("Axes Toggle")

    def _toggle_origin(self) -> None:
        """Toggle world origin marker state for this viewport only."""

        state = self._camera.state
        state.origin_visible = not bool(getattr(state, "origin_visible", True))
        self._sync_state()
        self._camera_updated("Origin Toggle")

    def _camera_settings(self) -> None:
        """Notify that camera settings were requested."""

        self.cameraChanged.emit("Camera Settings")

    def _viewport_settings(self) -> None:
        """Notify that viewport settings were requested."""

        self.cameraChanged.emit("Viewport Settings")

    def _camera_updated(self, reason: str) -> None:
        """Refresh the owning viewport after a camera state change."""

        self._sync_state()
        if self._update_callback is not None:
            self._update_callback()
        parent = self.parentWidget()
        if parent is not None:
            parent.update()
        self.cameraChanged.emit(reason)

    def _sync_state(self) -> None:
        """Synchronize button state from the active viewport camera state."""

        state = self._camera.state
        projection = getattr(state, "projection_mode", "perspective")
        self._buttons["projection"].setChecked(projection == "orthographic")
        self._buttons["projection"].setText(
            "ORT" if projection == "orthographic" else "PER"
        )
        self._buttons["grid"].setChecked(bool(getattr(state, "grid_visible", True)))
        self._buttons["axes"].setChecked(bool(getattr(state, "axis_visible", True)))
        self._buttons["origin"].setChecked(bool(getattr(state, "origin_visible", True)))
        self._buttons["orbit"].setChecked(self._navigation_mode == "orbit")
        self._buttons["pan"].setChecked(self._navigation_mode == "pan")

    def _entities(self) -> list[Any]:
        """Return visible shared-scene entities from the injected provider."""

        if self._entities_provider is None:
            return []

        entities = self._entities_provider()
        if entities is None:
            return []
        return list(entities)

    def _selection(self) -> list[Any]:
        """Return selected shared-scene entities from the injected provider."""

        if self._selection_provider is None:
            return []

        selected = self._selection_provider()
        if selected is None:
            return []
        return list(selected)

    def _bounds_from(self, entities: Iterable[Any]) -> BoundingBox3D:
        """Build a 3D bounding box from entities without owning geometry."""

        bounds = BoundingBox3D()
        for entity in entities:
            box = getattr(entity, "bounding_box3d", None)
            if callable(box):
                box = box()
            if box is None or not getattr(box, "valid", False):
                continue
            for corner in box.corners():
                bounds.add(corner)
        return bounds
