from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QEvent, QSettings, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QDockWidget, QMainWindow, QWidget


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
            dock = widget.parentWidget()
            if isinstance(dock, QDockWidget):
                dock.hide()

    def opened_panels(self) -> tuple[str, ...]:
        """Return ids for all tracked singleton panels."""

        return tuple(self._widgets.keys())


class WorkspaceDockWidget(QDockWidget):
    """Dock widget that hides instead of destroying registered panels."""

    def closeEvent(self, event) -> None:
        """Hide the dock panel while preserving the widget instance."""

        event.ignore()
        self.hide()


class PanelPresentationController(QObject):
    """Presents panels through Qt docking and remembers panel geometry."""

    def __init__(
        self,
        main_window: QMainWindow | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Create a presentation controller for dockable panels."""

        super().__init__(parent)

        self._main_window = main_window
        self._geometry_by_widget: dict[QWidget, bytes] = {}
        self._dock_by_widget: dict[QWidget, QDockWidget] = {}

    def create_dock(
        self,
        panel_id: str,
        panel_definition: PanelDefinition,
        widget: QWidget,
    ) -> QDockWidget | None:
        """Create a QDockWidget for a lazily instantiated panel."""

        if self._main_window is None:
            return None

        dock = WorkspaceDockWidget(panel_definition.title, self._main_window)
        dock.setObjectName(f"WorkspaceDock_{panel_id}")
        dock.setWidget(widget)
        dock.setMinimumSize(
            max(240, panel_definition.default_size.width() // 2),
            180,
        )
        dock.resize(panel_definition.default_size)
        dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        dock.installEventFilter(self)
        widget.installEventFilter(self)

        self._main_window.addDockWidget(
            self._dock_area(panel_definition),
            dock,
        )
        dock.hide()
        self._dock_by_widget[widget] = dock
        return dock

    def dock_for(self, widget: QWidget) -> QDockWidget | None:
        """Return the dock that hosts a panel widget when one exists."""

        return self._dock_by_widget.get(widget)

    def show_panel(self, widget: QWidget) -> None:
        """Show a panel as a dock or non-modal utility window."""

        dock = self.dock_for(widget)
        if dock is not None:
            dock.show()
            self.raise_panel(widget)
            return

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
        dock = self.dock_for(widget)
        if dock is not None:
            dock.hide()
        else:
            widget.hide()

    def raise_panel(self, widget: QWidget) -> None:
        """Raise and activate a visible panel surface."""

        dock = self.dock_for(widget)
        if dock is not None:
            dock.raise_()
            return

        widget.raise_()
        widget.activateWindow()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Remember panel geometry when a managed panel closes or hides."""

        if isinstance(watched, QWidget) and event.type() in {
            QEvent.Type.Close,
            QEvent.Type.Hide,
        }:
            self._remember_geometry(watched)
        return super().eventFilter(watched, event)

    def _prepare_window(self, widget: QWidget) -> None:
        """Apply utility-window behavior when no QMainWindow host exists."""

        widget.setWindowFlag(Qt.WindowType.Tool, True)
        widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        widget.installEventFilter(self)

    def _remember_geometry(self, widget: QWidget) -> None:
        """Store the current geometry for a panel widget or dock."""

        dock = self.dock_for(widget)
        if dock is not None:
            self._geometry_by_widget[widget] = bytes(dock.saveGeometry())
        elif widget.isWindow():
            self._geometry_by_widget[widget] = bytes(widget.saveGeometry())

    def _dock_area(
        self,
        panel_definition: PanelDefinition,
    ) -> Qt.DockWidgetArea:
        """Return a professional default dock area for a panel category."""

        category = (panel_definition.category or "").lower()
        if category in {"cad", "project", "reference"}:
            return Qt.DockWidgetArea.LeftDockWidgetArea
        if category in {"bim", "coordination", "ai"}:
            return Qt.DockWidgetArea.RightDockWidgetArea
        return Qt.DockWidgetArea.RightDockWidgetArea


class WorkspacePanelManager(QObject):
    """Central manager for lazily opened dockable workspace panels."""

    panelOpened = Signal(str)
    panelClosed = Signal(str)
    layoutSaved = Signal(str)
    layoutLoaded = Signal(str)

    PRESETS: dict[str, tuple[str, ...]] = {
        "Architect": (
            "explorer",
            "layer_manager",
            "reference_browser",
            "coordination",
        ),
        "Mechanical": (
            "explorer",
            "layer_manager",
            "dimension_manager",
            "constraint_manager",
        ),
        "Product Design": (
            "explorer",
            "block_manager",
            "pattern_manager",
            "selection_sets",
        ),
        "Visualization": (
            "explorer",
            "project_manager",
            "reference_layers",
            "clash_dashboard",
        ),
    }

    def __init__(self, parent: QObject | None = None) -> None:
        """Create the workspace panel manager and its controllers."""

        super().__init__(parent)

        self.registry = PanelRegistry()
        self.factory = PanelFactory()
        self.lifecycle = PanelLifecycleController()
        self.presentation = PanelPresentationController(
            parent if isinstance(parent, QMainWindow) else None,
            self,
        )
        self._main_window = parent if isinstance(parent, QMainWindow) else None
        self._panel_ids_by_widget: dict[QWidget, str] = {}
        self._dock_by_panel_id: dict[str, QDockWidget] = {}
        self._restored_startup_layout = False
        self._settings = QSettings("Freeman Creations House", "Kinematics Studio")

        if self._main_window is not None:
            self._main_window.setDockNestingEnabled(True)
            self._main_window.setDockOptions(
                QMainWindow.DockOption.AllowNestedDocks
                | QMainWindow.DockOption.AllowTabbedDocks
                | QMainWindow.DockOption.AnimatedDocks
                | QMainWindow.DockOption.GroupedDragging
            )
        app = None
        try:
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
        except RuntimeError:
            app = None
        if app is not None:
            app.aboutToQuit.connect(self.save_startup_layout)
        QTimer.singleShot(0, self.restore_startup_layout)

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
            dock = self.presentation.create_dock(panel_id, definition, widget)
            if dock is not None:
                self._dock_by_panel_id[panel_id] = dock
                dock.visibilityChanged.connect(
                    lambda visible, current_panel_id=panel_id: (
                        self._on_dock_visibility_changed(
                            current_panel_id,
                            visible,
                        )
                    )
                )

        self.presentation.show_panel(widget)
        self._tabify_category_peers(panel_id)
        self.panelOpened.emit(panel_id)
        return widget

    def close_panel(self, panel_id: str) -> None:
        """Close a panel by hiding the tracked singleton instance."""

        widget = self.lifecycle.widget(panel_id)
        if widget is not None:
            self.presentation.hide_panel(widget)
            self.panelClosed.emit(panel_id)

    def toggle_panel(self, panel_id: str) -> QWidget | None:
        """Toggle a registered panel between visible and hidden states."""

        widget = self.lifecycle.widget(panel_id)
        dock = self._dock_by_panel_id.get(panel_id)
        if widget is not None:
            visible = dock.isVisible() if dock is not None else widget.isVisible()
            if visible:
                self.presentation.hide_panel(widget)
                self.panelClosed.emit(panel_id)
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

    def save_current_layout(self, name: str = "Current") -> None:
        """Persist the current Qt dock layout under a workspace layout name."""

        if self._main_window is None:
            return
        self._settings.setValue(
            f"workspace_layouts/{name}/state",
            self._main_window.saveState(),
        )
        self._settings.setValue(
            f"workspace_layouts/{name}/open_panels",
            list(self._visible_panel_ids()),
        )
        self.layoutSaved.emit(name)

    def save_startup_layout(self) -> None:
        """Persist the current layout for automatic startup restoration."""

        self.save_current_layout("Startup")

    def load_layout(self, name: str = "Current") -> bool:
        """Load a persisted Qt dock layout by name."""

        if self._main_window is None:
            return False

        panel_ids = self._settings.value(
            f"workspace_layouts/{name}/open_panels",
            [],
        )
        for panel_id in self._coerce_panel_ids(panel_ids):
            if self.registry.contains(panel_id):
                self.open_panel(panel_id)

        state = self._settings.value(f"workspace_layouts/{name}/state")
        if state:
            restored = self._main_window.restoreState(state)
            if restored:
                self.layoutLoaded.emit(name)
            return bool(restored)
        return False

    def restore_startup_layout(self) -> bool:
        """Restore the last saved startup layout once panels are registered."""

        if self._restored_startup_layout:
            return False
        self._restored_startup_layout = True
        return self.load_layout("Startup")

    def reset_layout(self) -> None:
        """Hide all non-permanent panels and restore the viewport-first layout."""

        for panel_id in self.opened_panels():
            self.close_panel(panel_id)
        self.save_current_layout("Default")
        self.layoutLoaded.emit("Default")

    def restore_default_layout(self) -> None:
        """Restore the default viewport-first workspace layout."""

        self.reset_layout()

    def apply_preset(self, name: str) -> None:
        """Open a professional workspace preset by name."""

        for panel_id in self.PRESETS.get(name, ()):
            if self.registry.contains(panel_id):
                self.open_panel(panel_id)
        self.save_current_layout(name)
        self.layoutLoaded.emit(name)

    def available_presets(self) -> tuple[str, ...]:
        """Return the built-in professional workspace preset names."""

        return tuple(self.PRESETS)

    def _tabify_category_peers(self, panel_id: str) -> None:
        """Tabify visible docks in the same category when practical."""

        if self._main_window is None:
            return
        current = self._dock_by_panel_id.get(panel_id)
        if current is None:
            return
        definition = self.registry.definition(panel_id)
        for other_id, other in self._dock_by_panel_id.items():
            if other_id == panel_id or not other.isVisible():
                continue
            other_definition = self.registry.definition(other_id)
            if other_definition.category == definition.category:
                self._main_window.tabifyDockWidget(other, current)
                current.raise_()
                return

    def _on_destroyed(self, panel_id: str) -> None:
        """Forget a panel when Qt destroys its widget."""

        widget = self.lifecycle.widget(panel_id)
        if widget is not None:
            self._panel_ids_by_widget.pop(widget, None)
        self._dock_by_panel_id.pop(panel_id, None)
        self.lifecycle.unregister(panel_id)

    def _on_dock_visibility_changed(self, panel_id: str, visible: bool) -> None:
        """Emit panel visibility state and remember layout changes."""

        if visible:
            self.panelOpened.emit(panel_id)
        else:
            self.panelClosed.emit(panel_id)
        QTimer.singleShot(0, self.save_startup_layout)

    def _coerce_panel_ids(self, value) -> tuple[str, ...]:
        """Convert QSettings list values into a tuple of panel ids."""

        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, (list, tuple)):
            return tuple(str(item) for item in value if str(item))
        return ()

    def _visible_panel_ids(self) -> tuple[str, ...]:
        """Return panel ids for currently visible dock panels."""

        visible_ids: list[str] = []
        for panel_id in self.opened_panels():
            dock = self._dock_by_panel_id.get(panel_id)
            widget = self.lifecycle.widget(panel_id)
            if dock is not None and dock.isVisible():
                visible_ids.append(panel_id)
            elif dock is None and widget is not None and widget.isVisible():
                visible_ids.append(panel_id)
        return tuple(visible_ids)
