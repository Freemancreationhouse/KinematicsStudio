from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget


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

        self._stack.addWidget(self._canvas)
        self._stack.addWidget(self._viewport3d)
        self._stack.setCurrentWidget(self._canvas)
        self._stack.currentChanged.connect(self._on_current_changed)

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

    def _on_current_changed(self, index: int) -> None:
        """Emit the public active-view signal when the stacked view changes."""

        widget = self._stack.widget(index)
        view_name = "3d" if widget is self._viewport3d else "2d"
        if view_name != self._active_view_name:
            self._active_view_name = view_name
            self.active_view_changed.emit(view_name)
