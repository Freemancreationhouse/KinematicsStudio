from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QEvent, QSize, Qt
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class PanelDefinition:
    """Registration metadata for an on-demand workspace panel."""

    id: str
    title: str
    factory: Callable[[], QWidget]
    singleton: bool
    default_size: QSize
    category: str | None = None


class PanelRegistry:
    """Registry of panel definitions available to the workspace shell."""

    def __init__(self) -> None:
        """Create an empty panel registry."""

        self._definitions: dict[str, PanelDefinition] = {}

    def register(self, panel_definition: PanelDefinition) -> None:
        """Register or replace a panel definition."""

        if not panel_definition.id.strip():
            raise ValueError("Panel id must not be empty.")
        if not panel_definition.title.strip():
            raise ValueError("Panel title must not be empty.")

        self._definitions[panel_definition.id] = panel_definition

    def contains(self, panel_id: str) -> bool:
        """Return True when a panel id is registered."""

        return panel_id in self._definitions

    def definition(self, panel_id: str) -> PanelDefinition:
        """Return the registered definition for a panel id."""

        try:
            return self._definitions[panel_id]
        except KeyError as exc:
            raise KeyError(f"Unknown workspace panel: {panel_id}") from exc

    def definitions(self) -> tuple[PanelDefinition, ...]:
        """Return all registered panel definitions."""

        return tuple(self._definitions.values())


class PanelFactory:
    """Lazy factory for creating panel widgets from registered definitions."""

    def create(self, panel_definition: PanelDefinition) -> QWidget:
        """Create a panel widget from its registered factory."""

        widget = panel_definition.factory()
        if not isinstance(widget, QWidget):
            raise TypeError(
                f"Panel factory for {panel_definition.id} did not return QWidget."
            )
        widget.setWindowTitle(panel_definition.title)
        return widget


class PanelLifecycleController:
    """Tracks opened singleton panels and prevents duplicate instances."""

    def __init__(self) -> None:
        """Create an empty lifecycle controller."""

        self._widgets: dict[str, QWidget] = {}

    def is_open(self, panel_id: str) -> bool:
        """Return True when a singleton panel has an active widget."""

        return panel_id in self._widgets

    def widget(self, panel_id: str) -> QWidget | None:
        """Return a tracked singleton widget by panel id."""

        return self._widgets.get(panel_id)

    def register(self, panel_id: str, widget: QWidget) -> None:
        """Track a singleton panel widget."""

        self._widgets[panel_id] = widget

    def unregister(self, panel_id: str) -> None:
        """Stop tracking a singleton panel widget."""

        self._widgets.pop(panel_id, None)

    def close_all(self) -> None:
        """Hide all tracked singleton panels without destroying them."""

        for widget in self._widgets.values():
            widget.hide()

    def opened_panels(self) -> tuple[str, ...]:
        """Return ids for all tracked singleton panels."""

        return tuple(self._widgets.keys())


class PanelPresentationController(QObject):
    """Presents panels as non-modal utility windows and remembers geometry."""

    def __init__(self, parent: QObject | None = None) -> None:
        """Create a presentation controller."""

        super().__init__(parent)

        self._geometry_by_widget: dict[QWidget, bytes] = {}

    def show_panel(self, widget: QWidget) -> None:
        """Show a panel as a non-modal utility window."""

        self._prepare_window(widget)
        geometry = self._geometry_by_widget.get(widget)
        if geometry:
            widget.restoreGeometry(geometry)
        elif not widget.size().isValid() or widget.size().isEmpty():
            widget.resize(420, 520)

        widget.show()
        self.raise_panel(widget)

    def hide_panel(self, widget: QWidget) -> None:
        """Hide a panel after storing its current geometry."""

        self._remember_geometry(widget)
        widget.hide()

    def raise_panel(self, widget: QWidget) -> None:
        """Raise and activate a visible panel window."""

        widget.raise_()
        widget.activateWindow()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Remember panel geometry when a managed panel closes or hides."""

        if isinstance(watched, QWidget) and event.type() in {
            QEvent.Close,
            QEvent.Hide,
        }:
            self._remember_geometry(watched)
        return super().eventFilter(watched, event)

    def _prepare_window(self, widget: QWidget) -> None:
        """Apply utility-window behavior to a panel widget."""

        widget.setWindowFlag(Qt.Tool, True)
        widget.setAttribute(Qt.WA_DeleteOnClose, False)
        widget.installEventFilter(self)

    def _remember_geometry(self, widget: QWidget) -> None:
        """Store the current geometry for a panel widget."""

        if widget.isWindow():
            self._geometry_by_widget[widget] = bytes(widget.saveGeometry())


class WorkspacePanelManager(QObject):
    """Central manager for lazily opened non-permanent workspace panels."""

    def __init__(self, parent: QObject | None = None) -> None:
        """Create the workspace panel manager and its controllers."""

        super().__init__(parent)

        self.registry = PanelRegistry()
        self.factory = PanelFactory()
        self.lifecycle = PanelLifecycleController()
        self.presentation = PanelPresentationController(self)
        self._panel_ids_by_widget: dict[QWidget, str] = {}

    def register_panel(
        self,
        panel_id: str,
        title: str,
        factory: Callable[[], QWidget],
        singleton: bool = True,
        default_size: QSize | None = None,
        category: str | None = None,
    ) -> None:
        """Register a panel for lazy on-demand creation."""

        self.registry.register(
            PanelDefinition(
                id=panel_id,
                title=title,
                factory=factory,
                singleton=singleton,
                default_size=default_size or QSize(420, 520),
                category=category,
            )
        )

    def open_panel(self, panel_id: str) -> QWidget:
        """Open a registered panel and return its widget."""

        definition = self.registry.definition(panel_id)
        widget = self.lifecycle.widget(panel_id) if definition.singleton else None

        if widget is None:
            widget = self.factory.create(definition)
            widget.resize(definition.default_size)
            self._panel_ids_by_widget[widget] = panel_id
            widget.destroyed.connect(
                lambda _=None, current_panel_id=panel_id: self._on_destroyed(
                    current_panel_id
                )
            )
            if definition.singleton:
                self.lifecycle.register(panel_id, widget)

        self.presentation.show_panel(widget)
        return widget

    def close_panel(self, panel_id: str) -> None:
        """Close a panel by hiding the tracked singleton instance."""

        widget = self.lifecycle.widget(panel_id)
        if widget is not None:
            self.presentation.hide_panel(widget)

    def toggle_panel(self, panel_id: str) -> QWidget | None:
        """Toggle a registered panel between visible and hidden states."""

        widget = self.lifecycle.widget(panel_id)
        if widget is not None and widget.isVisible():
            self.presentation.hide_panel(widget)
            return widget
        return self.open_panel(panel_id)

    def refresh_panel(self, panel_id: str) -> None:
        """Refresh a panel when it exposes a refresh method."""

        widget = self.lifecycle.widget(panel_id)
        if widget is not None:
            refresh = getattr(widget, "refresh", None)
            if callable(refresh):
                refresh()

    def refresh_all(self) -> None:
        """Refresh every opened singleton panel that supports refresh."""

        for panel_id in self.lifecycle.opened_panels():
            self.refresh_panel(panel_id)

    def opened_panels(self) -> tuple[str, ...]:
        """Return ids for all opened singleton panels."""

        return self.lifecycle.opened_panels()

    def _on_destroyed(self, panel_id: str) -> None:
        """Forget a panel when Qt destroys its widget."""

        widget = self.lifecycle.widget(panel_id)
        if widget is not None:
            self._panel_ids_by_widget.pop(widget, None)
        self.lifecycle.unregister(panel_id)
