from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import count
from typing import Any, Callable

from PySide6.QtCore import QObject, QEvent, Signal
from PySide6.QtWidgets import QWidget

try:
    import shiboken6
except ImportError:  # pragma: no cover - PySide runtime dependency.
    shiboken6 = None


class ViewportType(str, Enum):
    """Supported professional viewport types."""

    PERSPECTIVE = "Perspective"
    TOP = "Top"
    FRONT = "Front"
    RIGHT = "Right"
    LEFT = "Left"
    BACK = "Back"
    BOTTOM = "Bottom"
    USER = "User"
    CAMERA = "Camera"
    SECTION = "Section"


class ViewportLayout(str, Enum):
    """Supported multi-viewport layout names."""

    SINGLE = "Single"
    DUAL_HORIZONTAL = "Dual Horizontal"
    DUAL_VERTICAL = "Dual Vertical"
    TRIPLE = "Triple View"
    QUAD = "Quad"
    CUSTOM = "Custom"


@dataclass(frozen=True)
class ViewportRegistration:
    """Immutable registration metadata for one managed viewport."""

    viewport_id: str
    viewport_type: ViewportType
    widget: QWidget
    camera: Any
    renderer: Any
    overlay_manager: Any
    toolbar: Any
    dock_container: QWidget | None
    workspace_provider: Any


@dataclass(frozen=True)
class ViewportEvent:
    """Event payload broadcast by the viewport manager."""

    name: str
    viewport_id: str
    viewport_type: ViewportType | None = None
    layout: ViewportLayout | None = None


@dataclass
class ViewportOverlayManager:
    """Per-viewport overlay visibility registry owned by the UI framework."""

    viewport_id: str
    visible_overlays: set[str] = field(default_factory=set)

    def set_visible(self, overlay_id: str, visible: bool) -> None:
        """Set overlay visibility metadata for a viewport."""

        if visible:
            self.visible_overlays.add(overlay_id)
        else:
            self.visible_overlays.discard(overlay_id)

    def is_visible(self, overlay_id: str) -> bool:
        """Return True when an overlay id is marked visible."""

        return overlay_id in self.visible_overlays


@dataclass(frozen=True)
class ViewportToolbar:
    """Per-viewport toolbar metadata for future visible toolbar controls."""

    viewport_id: str
    action_ids: tuple[str, ...] = ()


class ViewportRegistry:
    """Registry for all viewports managed by the UI viewport framework."""

    def __init__(self) -> None:
        """Create an empty viewport registry."""

        self._viewports: dict[str, ViewportRegistration] = {}

    def register(self, registration: ViewportRegistration) -> None:
        """Register or replace one viewport registration."""

        if not registration.viewport_id.strip():
            raise ValueError("Viewport id must not be empty.")
        self._viewports[registration.viewport_id] = registration

    def unregister(self, viewport_id: str) -> None:
        """Remove one viewport registration."""

        self._viewports.pop(viewport_id, None)

    def contains(self, viewport_id: str) -> bool:
        """Return True when a viewport id is registered."""

        return viewport_id in self._viewports

    def get(self, viewport_id: str) -> ViewportRegistration | None:
        """Return a registered viewport by id."""

        return self._viewports.get(viewport_id)

    def all(self) -> tuple[ViewportRegistration, ...]:
        """Return all registered viewport records."""

        return tuple(self._viewports.values())

    def ids(self) -> tuple[str, ...]:
        """Return all registered viewport ids."""

        return tuple(self._viewports)


class ViewportManager(QObject):
    """Infrastructure manager for synchronized professional viewports."""

    viewportCreated = Signal(str)
    viewportDestroyed = Signal(str)
    viewportFocused = Signal(str)
    viewportActivated = Signal(str)
    layoutChanged = Signal(str)
    viewportRenamed = Signal(str, str)
    viewportClosed = Signal(str)
    viewportEvent = Signal(object)

    _id_counter = count(1)

    def __init__(
        self,
        *,
        workspace_provider: Any = None,
        parent: QObject | None = None,
    ) -> None:
        """Create an empty manager without owning scene or geometry data."""

        super().__init__(parent)

        self.registry = ViewportRegistry()
        self._workspace_provider = workspace_provider
        self._active_viewport_id: str | None = None
        self._focused_viewport_id: str | None = None
        self._layout = ViewportLayout.SINGLE
        self._viewport_ids_by_widget: dict[QWidget, str] = {}
        self._names: dict[str, str] = {}
        self._destroyed_slots: dict[str, Callable[..., None]] = {}
        self._disposing = False
        self.destroyed.connect(lambda obj=None: self._mark_disposing())

    def create_viewport(
        self,
        *,
        viewport_type: ViewportType | str,
        factory: Callable[[], QWidget],
        camera: Any = None,
        renderer: Any = None,
        overlay_manager: Any = None,
        toolbar: Any = None,
        dock_container: QWidget | None = None,
        viewport_id: str | None = None,
    ) -> ViewportRegistration:
        """Create, register and return one viewport from a widget factory."""

        widget = factory()
        if not isinstance(widget, QWidget):
            raise TypeError("Viewport factory must return a QWidget.")
        return self.register_viewport(
            widget=widget,
            viewport_type=viewport_type,
            camera=camera,
            renderer=renderer,
            overlay_manager=overlay_manager,
            toolbar=toolbar,
            dock_container=dock_container,
            viewport_id=viewport_id,
        )

    def register_viewport(
        self,
        *,
        widget: QWidget,
        viewport_type: ViewportType | str,
        camera: Any = None,
        renderer: Any = None,
        overlay_manager: Any = None,
        toolbar: Any = None,
        dock_container: QWidget | None = None,
        viewport_id: str | None = None,
    ) -> ViewportRegistration:
        """Register an externally owned viewport without taking scene ownership."""

        normalized_type = self._viewport_type(viewport_type)
        resolved_id = viewport_id or self._next_id(normalized_type)
        registration = ViewportRegistration(
            viewport_id=resolved_id,
            viewport_type=normalized_type,
            widget=widget,
            camera=camera,
            renderer=renderer,
            overlay_manager=overlay_manager
            or ViewportOverlayManager(resolved_id),
            toolbar=toolbar or ViewportToolbar(resolved_id),
            dock_container=dock_container,
            workspace_provider=self._workspace_provider,
        )
        self.registry.register(registration)
        self._viewport_ids_by_widget[widget] = resolved_id
        self._names.setdefault(resolved_id, normalized_type.value)
        widget.installEventFilter(self)
        destroyed_slot = lambda obj=None, viewport_id=resolved_id: (
            self._cleanup_destroyed_viewport(viewport_id)
        )
        widget.destroyed.connect(destroyed_slot)
        self._destroyed_slots[resolved_id] = destroyed_slot
        if self._active_viewport_id is None:
            self.set_active_viewport(resolved_id)
        self._emit("ViewportCreated", resolved_id)
        self._emit_signal("viewportCreated", resolved_id)
        return registration

    def destroy_viewport(self, viewport_id: str) -> None:
        """Destroy a registered viewport framework record and close its widget."""

        registration = self.registry.get(viewport_id)
        if registration is None:
            return
        self._safe_remove_event_filter(registration.widget)
        self._cleanup_viewport_references(viewport_id, registration.widget)
        self._safe_close_widget(registration.widget)
        self._emit("ViewportDestroyed", viewport_id)
        self._emit_signal("viewportDestroyed", viewport_id)

    def close_viewport(self, viewport_id: str) -> None:
        """Close a viewport without modifying engineering data."""

        if not self.registry.contains(viewport_id):
            return
        self._emit("ViewportClosed", viewport_id)
        self._emit_signal("viewportClosed", viewport_id)

    def unregister_viewport(self, viewport_id: str) -> None:
        """Unregister one viewport without closing or deleting its widget."""

        registration = self.registry.get(viewport_id)
        if registration is None:
            return
        self._safe_remove_event_filter(registration.widget)
        self._cleanup_viewport_references(viewport_id, registration.widget)
        self._emit("ViewportDestroyed", viewport_id)
        self._emit_signal("viewportDestroyed", viewport_id)

    def shutdown(self) -> None:
        """Disconnect viewport callbacks before Qt object destruction."""

        if self._disposing:
            return
        self._disposing = True
        for registration in tuple(self.registry.all()):
            self._disconnect_destroyed_slot(
                registration.viewport_id,
                registration.widget,
            )
            self._safe_remove_event_filter(registration.widget)
        self.registry = ViewportRegistry()
        self._viewport_ids_by_widget.clear()
        self._names.clear()
        self._destroyed_slots.clear()
        self._active_viewport_id = None
        self._focused_viewport_id = None

    def set_active_viewport(self, viewport_id: str) -> None:
        """Set the single active viewport."""

        if not self.registry.contains(viewport_id):
            return
        if self._active_viewport_id == viewport_id:
            return
        self._active_viewport_id = viewport_id
        self._focused_viewport_id = viewport_id
        self._emit("ViewportActivated", viewport_id)
        self._emit_signal("viewportActivated", viewport_id)

    def set_focused_viewport(self, viewport_id: str) -> None:
        """Set the focused viewport and make it active."""

        if not self.registry.contains(viewport_id):
            return
        self._focused_viewport_id = viewport_id
        self._emit("ViewportFocused", viewport_id)
        self._emit_signal("viewportFocused", viewport_id)
        self.set_active_viewport(viewport_id)

    def active_viewport_id(self) -> str | None:
        """Return the active viewport id."""

        return self._active_viewport_id

    def focused_viewport_id(self) -> str | None:
        """Return the focused viewport id."""

        return self._focused_viewport_id

    def active_viewport(self) -> ViewportRegistration | None:
        """Return the active viewport registration."""

        if self._active_viewport_id is None:
            return None
        return self.registry.get(self._active_viewport_id)

    def focused_viewport(self) -> ViewportRegistration | None:
        """Return the focused viewport registration."""

        if self._focused_viewport_id is None:
            return None
        return self.registry.get(self._focused_viewport_id)

    def rename_viewport(self, viewport_id: str, name: str) -> None:
        """Rename one viewport for UI presentation."""

        if not self.registry.contains(viewport_id):
            return
        self._names[viewport_id] = name
        self._emit("ViewportRenamed", viewport_id)
        self._emit_signal("viewportRenamed", viewport_id, name)

    def viewport_name(self, viewport_id: str) -> str:
        """Return the display name for a viewport."""

        return self._names.get(viewport_id, viewport_id)

    def set_layout(self, layout: ViewportLayout | str) -> None:
        """Set the current multi-viewport layout mode."""

        normalized_layout = self._viewport_layout(layout)
        if self._layout == normalized_layout:
            return
        self._layout = normalized_layout
        self._emit("LayoutChanged", self._active_viewport_id or "")
        self._emit_signal("layoutChanged", normalized_layout.value)

    def layout(self) -> ViewportLayout:
        """Return the current viewport layout mode."""

        return self._layout

    def viewports(self) -> tuple[ViewportRegistration, ...]:
        """Return all registered viewports."""

        return self.registry.all()

    def viewport_ids(self) -> tuple[str, ...]:
        """Return all registered viewport ids."""

        return self.registry.ids()

    def workspace(self) -> Any:
        """Return the current shared workspace from the injected provider."""

        provider = self._workspace_provider
        if provider is None:
            return None
        workspace = getattr(provider, "workspace", None)
        return workspace() if callable(workspace) else workspace

    def scene(self) -> Any:
        """Return the current shared scene from the active workspace."""

        workspace = self.workspace()
        if workspace is None:
            return None
        scene = getattr(workspace, "scene", None)
        return scene() if callable(scene) else scene

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Track focus and mouse activation for managed viewport widgets."""

        if self._disposing or not self._is_qobject_valid(self):
            return False
        if isinstance(watched, QWidget):
            viewport_id = self._viewport_ids_by_widget.get(watched)
            if viewport_id is not None and event.type() in {
                QEvent.Type.FocusIn,
                QEvent.Type.MouseButtonPress,
            }:
                self.set_focused_viewport(viewport_id)
        return super().eventFilter(watched, event)

    def _cleanup_destroyed_viewport(self, viewport_id: str) -> None:
        """Remove all manager references after Qt destroys a viewport widget."""

        if self._disposing or not self._is_qobject_valid(self):
            return
        registration = self.registry.get(viewport_id)
        if (
            registration is None
            and viewport_id not in self._names
            and viewport_id not in self._viewport_ids_by_widget.values()
        ):
            return
        widget = registration.widget if registration is not None else None
        self._cleanup_viewport_references(viewport_id, widget)
        self._emit("ViewportDestroyed", viewport_id)
        self._emit_signal("viewportDestroyed", viewport_id)

    def _cleanup_viewport_references(
        self,
        viewport_id: str,
        widget: QWidget | None,
    ) -> None:
        """Remove registry, focus and active references for one viewport."""

        self.registry.unregister(viewport_id)
        if widget is not None:
            self._disconnect_destroyed_slot(viewport_id, widget)
            self._viewport_ids_by_widget.pop(widget, None)
        for tracked_widget, tracked_id in tuple(self._viewport_ids_by_widget.items()):
            if tracked_id == viewport_id:
                self._viewport_ids_by_widget.pop(tracked_widget, None)
        self._names.pop(viewport_id, None)
        if self._active_viewport_id == viewport_id:
            ids = self.registry.ids()
            self._active_viewport_id = ids[0] if ids else None
        if self._focused_viewport_id == viewport_id:
            self._focused_viewport_id = self._active_viewport_id

    def _safe_remove_event_filter(self, widget: QWidget) -> None:
        """Remove the event filter without failing on deleted Qt wrappers."""

        try:
            widget.removeEventFilter(self)
        except RuntimeError:
            pass

    def _disconnect_destroyed_slot(
        self,
        viewport_id: str,
        widget: QWidget,
    ) -> None:
        """Disconnect the stored destroyed callback for one viewport widget."""

        slot = self._destroyed_slots.pop(viewport_id, None)
        if slot is None:
            return
        try:
            widget.destroyed.disconnect(slot)
        except (RuntimeError, TypeError):
            pass

    def _safe_close_widget(self, widget: QWidget) -> None:
        """Close and delete a viewport widget without stale manager references."""

        try:
            widget.close()
            widget.deleteLater()
        except RuntimeError:
            pass

    def _emit(self, event_name: str, viewport_id: str) -> None:
        """Broadcast a typed viewport manager event."""

        if self._disposing or not self._is_qobject_valid(self):
            return
        registration = self.registry.get(viewport_id)
        viewport_type = registration.viewport_type if registration else None
        self._emit_signal(
            "viewportEvent",
            ViewportEvent(
                name=event_name,
                viewport_id=viewport_id,
                viewport_type=viewport_type,
                layout=self._layout,
            ),
        )

    def _emit_signal(self, signal_name: str, *args: Any) -> None:
        """Emit a Qt signal only while this QObject is still valid."""

        if self._disposing or not self._is_qobject_valid(self):
            return
        try:
            signal = getattr(self, signal_name)
            signal.emit(*args)
        except (AttributeError, RuntimeError):
            pass

    def _mark_disposing(self) -> None:
        """Mark this manager as disposing without emitting any signals."""

        self._disposing = True

    def _is_qobject_valid(self, obj: QObject) -> bool:
        """Return True when a QObject wrapper still has a live C++ object."""

        if shiboken6 is None:
            return True
        try:
            return bool(shiboken6.isValid(obj))
        except RuntimeError:
            return False

    def _next_id(self, viewport_type: ViewportType) -> str:
        """Create a stable unique id for a viewport registration."""

        base = viewport_type.value.lower().replace(" ", "_")
        return f"{base}_{next(self._id_counter)}"

    def _viewport_type(self, value: ViewportType | str) -> ViewportType:
        """Normalize a viewport type value."""

        if isinstance(value, ViewportType):
            return value
        for viewport_type in ViewportType:
            if viewport_type.value.lower() == str(value).lower():
                return viewport_type
        raise ValueError(f"Unsupported viewport type: {value}")

    def _viewport_layout(self, value: ViewportLayout | str) -> ViewportLayout:
        """Normalize a viewport layout value."""

        if isinstance(value, ViewportLayout):
            return value
        for layout in ViewportLayout:
            if layout.value.lower() == str(value).lower():
                return layout
        raise ValueError(f"Unsupported viewport layout: {value}")
