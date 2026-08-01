from __future__ import annotations

from typing import Any


class ViewportSynchronizationService:
    """Synchronize 2D and 3D viewport repaint state for one active scene.

    The service does not own the workspace, scene, cameras, geometry or
    viewport widgets. It resolves the current workspace at synchronization time
    and asks every injected viewport to refresh after scene, selection, command
    or camera events.
    """

    def __init__(self, *, workspace_provider: Any, viewport_area: Any) -> None:
        """Create a synchronization service for an injected viewport area."""

        self.workspace_provider = workspace_provider
        self.viewport_area = viewport_area

    def synchronize(
        self,
        event_name: str,
        payload: Any | None = None,
    ) -> None:
        """Refresh every viewport that observes the active workspace scene."""

        del event_name, payload
        for viewport in self.viewports():
            update = getattr(viewport, "update", None)
            if callable(update):
                try:
                    update()
                except RuntimeError:
                    self._discard_invalid_viewport(viewport)

    def viewports(self) -> tuple[Any, ...]:
        """Return all injected viewport widgets without creating new widgets."""

        candidates: list[Any] = []
        viewport_manager = self._viewport_manager()
        if viewport_manager is not None:
            registry = getattr(viewport_manager, "registry", None)
            records = registry.all() if registry is not None else ()
            for record in records:
                viewport = getattr(record, "widget", None)
                if viewport is not None and viewport not in candidates:
                    if self._is_live_viewport(viewport):
                        candidates.append(viewport)
                    else:
                        unregister = getattr(viewport_manager, "unregister_viewport", None)
                        if callable(unregister):
                            unregister(getattr(record, "viewport_id", ""))

        for accessor_name in ("canvas", "viewport3d"):
            accessor = getattr(self.viewport_area, accessor_name, None)
            viewport = accessor() if callable(accessor) else accessor
            if (
                viewport is not None
                and viewport not in candidates
                and self._is_live_viewport(viewport)
            ):
                candidates.append(viewport)
        return tuple(candidates)

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

        for viewport in self.viewports():
            app = getattr(viewport, "app", None)
            viewport_workspace = getattr(app, "workspace", None)
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

        try:
            object_name = getattr(viewport, "objectName", None)
            if callable(object_name):
                object_name()
            return True
        except RuntimeError:
            return False

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
