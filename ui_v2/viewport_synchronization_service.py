from __future__ import annotations

from types import SimpleNamespace
from typing import Any

try:
    import shiboken6
except ImportError:  # pragma: no cover - optional PySide runtime helper.
    shiboken6 = None


class ViewportSynchronizationService:
    """Synchronize viewport repaint state for one shared workspace scene.

    The service does not own the workspace, scene, cameras, geometry or
    viewport widgets. It resolves the current workspace at synchronization time
    and marks only affected viewport widgets dirty after scene, selection,
    layer, property, command or project lifecycle events.
    """

    WORKSPACE_STATE_EVENTS = {
        "FullRefresh",
        "ProjectOpened",
        "ProjectClosed",
        "ProjectRecovered",
        "WorkspaceChanged",
        "SceneChanged",
        "EntityAdded",
        "EntityRemoved",
        "EntityModified",
        "EntityVisibilityChanged",
        "SelectionChanged",
        "LayerChanged",
        "LayerVisibilityChanged",
        "LayerLockChanged",
        "ActiveLayerChanged",
        "PropertyChanged",
        "MaterialChanged",
        "DocumentModified",
        "CommandCompleted",
        "CommandHistoryChanged",
        "Undo",
        "Redo",
    }
    ACTIVE_VIEW_EVENTS = {
        "CameraChanged",
        "ViewChanged",
        "ViewportActivated",
        "ViewportFocused",
        "ViewportLayoutChanged",
    }
    NON_VIEW_EVENTS = {
        "ActiveToolChanged",
        "PanelChanged",
    }

    def __init__(self, *, workspace_provider: Any, viewport_area: Any) -> None:
        """Create a synchronization service for an injected viewport area."""

        self.workspace_provider = workspace_provider
        self.viewport_area = viewport_area
        self._dirty_viewport_ids: set[str] = set()
        self._last_flush_event: str | None = None
        self._flush_count = 0

    def synchronize(
        self,
        event_name: str,
        payload: Any | None = None,
    ) -> None:
        """Mark affected viewports dirty and flush the minimal redraw set."""

        self.mark_dirty(event_name, payload)
        self.flush(event_name)

    def mark_dirty(
        self,
        event_name: str,
        payload: Any | None = None,
    ) -> None:
        """Mark viewports affected by an application state event as dirty."""

        del payload
        event = str(event_name or "FullRefresh")

        if event in self.NON_VIEW_EVENTS:
            return

        if event in self.ACTIVE_VIEW_EVENTS:
            active = self.active_viewport()
            if active is not None:
                self._dirty_viewport_ids.add(getattr(active, "viewport_id", ""))
            return

        if event in self.WORKSPACE_STATE_EVENTS or not event:
            for record in self.visible_viewport_records():
                self._dirty_viewport_ids.add(getattr(record, "viewport_id", ""))
            return

        for record in self.visible_viewport_records():
            self._dirty_viewport_ids.add(getattr(record, "viewport_id", ""))

    def flush(self, event_name: str = "FullRefresh") -> None:
        """Update each dirty live viewport once and clear dirty state."""

        if not self._dirty_viewport_ids:
            return

        viewport_manager = self._viewport_manager()
        dirty_ids = tuple(
            viewport_id
            for viewport_id in self._dirty_viewport_ids
            if viewport_id
        )
        self._dirty_viewport_ids.clear()

        records = self._records_by_id(dirty_ids)
        if not records and viewport_manager is None:
            records = tuple(self._fallback_records())

        for record in records:
            viewport = getattr(record, "widget", None)
            if viewport is None:
                continue
            if not self._is_live_viewport(viewport):
                self._discard_invalid_viewport(viewport)
                continue
            if not self._is_visible_viewport(viewport):
                continue
            update = getattr(viewport, "update", None)
            if callable(update):
                try:
                    update()
                except RuntimeError:
                    self._discard_invalid_viewport(viewport)

        self._last_flush_event = event_name
        self._flush_count += 1

    def dirty_viewport_ids(self) -> tuple[str, ...]:
        """Return viewport ids currently waiting for a redraw."""

        return tuple(sorted(viewport_id for viewport_id in self._dirty_viewport_ids))

    def flush_count(self) -> int:
        """Return the number of dirty redraw flushes performed."""

        return self._flush_count

    def last_flush_event(self) -> str | None:
        """Return the event name that caused the most recent redraw flush."""

        return self._last_flush_event

    def viewports(self) -> tuple[Any, ...]:
        """Return all injected viewport widgets without creating new widgets."""

        return tuple(
            record.widget
            for record in self.viewport_records()
            if getattr(record, "widget", None) is not None
        )

    def viewport_records(self) -> tuple[Any, ...]:
        """Return all live viewport records without creating widgets."""

        candidates: list[Any] = []
        viewport_manager = self._viewport_manager()
        if viewport_manager is not None:
            registry = getattr(viewport_manager, "registry", None)
            records = registry.all() if registry is not None else ()
            for record in records:
                viewport = getattr(record, "widget", None)
                if viewport is not None and record not in candidates:
                    if self._is_live_viewport(viewport):
                        candidates.append(record)
                    else:
                        unregister = getattr(viewport_manager, "unregister_viewport", None)
                        if callable(unregister):
                            unregister(getattr(record, "viewport_id", ""))

        if candidates:
            return tuple(candidates)

        return tuple(self._fallback_records())

    def visible_viewport_records(self) -> tuple[Any, ...]:
        """Return live viewport records that are currently visible."""

        return tuple(
            record
            for record in self.viewport_records()
            if self._is_visible_viewport(getattr(record, "widget", None))
        )

    def active_viewport(self) -> Any | None:
        """Return the active viewport record when the manager exposes one."""

        viewport_manager = self._viewport_manager()
        if viewport_manager is None:
            return None

        active = getattr(viewport_manager, "active_viewport", None)
        record = active() if callable(active) else active
        if record is None:
            return None

        viewport = getattr(record, "widget", None)
        if viewport is not None and self._is_live_viewport(viewport):
            return record
        return None

    def _fallback_records(self) -> tuple[Any, ...]:
        """Return lightweight records for legacy direct viewport accessors."""

        records: list[Any] = []
        for accessor_name in ("canvas", "viewport3d"):
            accessor = getattr(self.viewport_area, accessor_name, None)
            viewport = accessor() if callable(accessor) else accessor
            if (
                viewport is not None
                and all(
                    getattr(record, "widget", None) is not viewport
                    for record in records
                )
                and self._is_live_viewport(viewport)
            ):
                records.append(
                    SimpleNamespace(
                        viewport_id=accessor_name,
                        widget=viewport,
                    )
                )
        return tuple(records)

    def active_scene(self) -> Any | None:
        """Return the current scene-like model object without taking ownership."""

        workspace = self._current_workspace()
        if workspace is None:
            return None
        scene = getattr(workspace, "scene", None)
        if scene is not None:
            return scene
        return workspace

    def verify_single_scene(self) -> bool:
        """Return True when all viewports resolve to the same active workspace."""

        workspace = self._current_workspace()
        if workspace is None:
            return False

        for record in self.viewport_records():
            viewport = getattr(record, "widget", None)
            app = getattr(viewport, "app", None)
            viewport_workspace = getattr(app, "workspace", None)
            if callable(viewport_workspace):
                viewport_workspace = viewport_workspace()
            if viewport_workspace is not None and viewport_workspace is not workspace:
                return False
        return True

    def _current_workspace(self) -> Any | None:
        """Resolve the active workspace through the injected provider."""

        provider = self.workspace_provider
        if provider is None:
            return None

        workspace_method = getattr(provider, "workspace", None)
        if callable(workspace_method):
            return workspace_method()

        workspace = getattr(provider, "workspace", None)
        if workspace is not None:
            return workspace

        current_workspace = getattr(provider, "current_workspace", None)
        if callable(current_workspace):
            return current_workspace()

        return None

    def _viewport_manager(self) -> Any | None:
        """Return the viewport manager exposed by the viewport area."""

        accessor = getattr(self.viewport_area, "viewport_manager", None)
        return accessor() if callable(accessor) else accessor

    def _is_live_viewport(self, viewport: Any) -> bool:
        """Return True when a viewport QObject wrapper is still usable."""

        if viewport is None:
            return False
        if shiboken6 is not None:
            try:
                if not shiboken6.isValid(viewport):
                    return False
            except Exception:
                pass
        try:
            object_name = getattr(viewport, "objectName", None)
            if callable(object_name):
                object_name()
            return True
        except RuntimeError:
            return False

    def _is_visible_viewport(self, viewport: Any) -> bool:
        """Return True when a viewport is live and visible enough to repaint."""

        if not self._is_live_viewport(viewport):
            return False

        try:
            is_visible = getattr(viewport, "isVisible", None)
            if callable(is_visible):
                return bool(is_visible())
        except RuntimeError:
            return False
        return True

    def _records_by_id(self, viewport_ids: tuple[str, ...]) -> tuple[Any, ...]:
        """Return live records matching the requested viewport ids."""

        if not viewport_ids:
            return ()

        wanted = set(viewport_ids)
        records = []
        for record in self.viewport_records():
            if getattr(record, "viewport_id", "") in wanted:
                records.append(record)
        return tuple(records)

    def _discard_invalid_viewport(self, viewport: Any) -> None:
        """Remove a deleted viewport from the manager registry if present."""

        viewport_manager = self._viewport_manager()
        if viewport_manager is None:
            return

        registry = getattr(viewport_manager, "registry", None)
        records = registry.all() if registry is not None else ()
        for record in records:
            if getattr(record, "widget", None) is viewport:
                unregister = getattr(viewport_manager, "unregister_viewport", None)
                if callable(unregister):
                    unregister(getattr(record, "viewport_id", ""))
                return
