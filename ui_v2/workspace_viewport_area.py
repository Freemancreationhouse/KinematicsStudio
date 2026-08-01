from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from ui_v2.viewport_manager import ViewportLayout, ViewportManager, ViewportType


class WorkspaceViewportArea(QWidget):
    """Reusable container for switching between 2D and 3D viewport widgets."""

    active_view_changed = Signal(str)

    def __init__(self, canvas: QWidget, viewport3d: QWidget, parent: QWidget | None = None):
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

        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._viewport3d)
        self._stack.setCurrentWidget(self._canvas)
        self._stack.currentChanged.connect(self._on_current_changed)
        self._register_initial_viewports()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._stack)

    def show_2d(self) -> None:
        """Make the 2D canvas the active viewport."""

        self._stack.setCurrentWidget(self._canvas)

    def show_3d(self) -> None:
        """Make the 3D viewport the active viewport."""

        self._stack.setCurrentWidget(self._viewport3d)

    def toggle_view(self) -> None:
        """Toggle between the 2D canvas and the 3D viewport."""

        if self._stack.currentWidget() is self._canvas:
            self.show_3d()
        else:
            self.show_2d()

    def active_view(self) -> QWidget:
        """Return the currently active viewport widget."""

        return self._stack.currentWidget()

    def canvas(self) -> QWidget:
        """Return the injected 2D canvas widget."""

        return self._canvas

    def viewport3d(self) -> QWidget:
        """Return the injected 3D viewport widget."""

        return self._viewport3d

    def viewport_manager(self) -> ViewportManager:
        """Return the viewport framework manager."""

        return self._viewport_manager

    def active_viewport_id(self) -> str | None:
        """Return the active viewport id from the manager."""

        return self._viewport_manager.active_viewport_id()

    def set_layout(self, layout: ViewportLayout | str) -> None:
        """Record the requested viewport layout mode without changing UI layout."""

        self._viewport_manager.set_layout(layout)

    def _register_initial_viewports(self) -> None:
        """Register the existing 2D and 3D viewport widgets with the manager."""

        app = getattr(self._canvas, "app", None)
        engine = getattr(app, "engine", None)
        self._viewport_manager.register_viewport(
            viewport_id="viewport_2d",
            viewport_type=ViewportType.TOP,
            widget=self._canvas,
            camera=getattr(self._canvas, "camera", None),
            renderer=getattr(engine, "renderer", None),
            overlay_manager=None,
            toolbar=None,
            dock_container=self,
        )
        self._viewport_manager.register_viewport(
            viewport_id="viewport_3d",
            viewport_type=ViewportType.PERSPECTIVE,
            widget=self._viewport3d,
            camera=getattr(app, "camera3d", None),
            renderer=getattr(engine, "renderer3d", None),
            overlay_manager=None,
            toolbar=None,
            dock_container=self,
        )
        self._viewport_manager.set_layout(ViewportLayout.SINGLE)
        self._viewport_manager.set_active_viewport("viewport_2d")

    def _on_current_changed(self, index: int) -> None:
        """Emit the public active-view signal when the stacked view changes."""

        widget = self._stack.widget(index)
        view_name = "3d" if widget is self._viewport3d else "2d"
        viewport_id = "viewport_3d" if view_name == "3d" else "viewport_2d"
        self._viewport_manager.set_active_viewport(viewport_id)
        if view_name != self._active_view_name:
            self._active_view_name = view_name
            self.active_view_changed.emit(view_name)
