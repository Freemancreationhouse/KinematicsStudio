from __future__ import annotations

from typing import Any

from engine.geometry import Vector3

from engine.gizmo.gizmo_context import GizmoContext
from engine.gizmo.gizmo_events import GizmoEvents
from engine.gizmo.gizmo_handles import GizmoType, _gizmo_type
from engine.gizmo.gizmo_picker import GizmoPickResult, GizmoPicker
from engine.gizmo.gizmo_renderer import GizmoRenderPacket, GizmoRenderer
from engine.gizmo.gizmo_session import GizmoSession
from engine.gizmo.gizmo_settings import GizmoSettings
from engine.gizmo.gizmo_state import GizmoState


class GizmoManager:
    """Authoritative controller for professional transform gizmos."""

    def __init__(
        self,
        *,
        settings: GizmoSettings | None = None,
        events: GizmoEvents | None = None,
        picker: GizmoPicker | None = None,
        renderer: GizmoRenderer | None = None,
    ) -> None:
        """Create a reusable gizmo manager."""

        self.settings = settings or GizmoSettings()
        self.events = events or GizmoEvents()
        self.picker = picker or GizmoPicker()
        self.renderer = renderer or GizmoRenderer()
        self.state = GizmoState()
        self._context: GizmoContext | None = None
        self._sessions: dict[str, GizmoSession] = {}
        self._active_session_id: str | None = None
        self._ai_requests: list[dict[str, Any]] = []

    def attach_context(self, context: GizmoContext) -> None:
        """Attach dependency-injected runtime context."""

        self._context = context
        self.state.viewport_id = context.viewport_id
        self.refresh_from_selection()
        self.events.emit("GizmoContextAttached", "", {"viewport_id": context.viewport_id})

    def configure(
        self,
        gizmo_type: GizmoType | str,
        *,
        origin: Any | None = None,
        viewport_id: str = "",
    ) -> None:
        """Configure the active gizmo type and origin."""

        self.state.configure_handles(gizmo_type)
        if origin is not None:
            self.state.origin = _vector3(origin)
            self.state.orientation.set_pivot(self.state.origin)
        if viewport_id:
            self.state.viewport_id = viewport_id
        self.state.metadata["screen_size"] = self.settings.normalized_size()
        self.events.emit(
            "GizmoConfigured",
            "",
            {"gizmo_type": self.state.gizmo_type.value, "origin": self.state.origin},
        )

    def refresh_from_selection(self) -> None:
        """Show or hide gizmo based on current selection."""

        context = self._context
        if context is None:
            self.state.visible = False
            return
        selected = context.selected_entities()
        self.state.selected_entities = selected
        self.state.visible = bool(selected) and self.settings.enabled
        if selected:
            self.state.origin = self._origin_for_selection(selected)
            self.state.orientation.set_pivot(self.state.origin)
        self.events.emit(
            "GizmoSelectionRefreshed",
            "",
            {"visible": self.state.visible, "selected_count": len(selected)},
        )

    def pick_handle(self, ray: Any) -> GizmoPickResult | None:
        """Pick and hover a gizmo handle."""

        result = self.picker.pick(
            self.state,
            ray,
            tolerance=self.settings.handle_pick_tolerance,
        )
        self.events.emit(
            "GizmoHandleHovered",
            "",
            {"handle_id": result.handle_id if result else ""},
        )
        return result

    def begin_drag(self, handle_id: str, point: Any) -> GizmoSession:
        """Begin dragging a handle in the active viewport."""

        context = self._require_context()
        session = GizmoSession(context, self.state, self.events)
        session.begin_drag(handle_id, point)
        self._sessions[session.session_id] = session
        self._active_session_id = session.session_id
        return session

    def update_drag(self, point: Any, session_id: str | None = None) -> None:
        """Update active gizmo drag."""

        session = self._resolve_session(session_id)
        if session is not None:
            session.update_drag(point)

    def commit(self, session_id: str | None = None) -> Any:
        """Commit active gizmo drag through delegated tools."""

        session = self._resolve_session(session_id)
        if session is None:
            return None
        result = session.commit()
        self._finish_session(session.session_id)
        self.refresh_from_selection()
        return result

    def cancel(self, session_id: str | None = None) -> None:
        """Cancel active gizmo drag."""

        session = self._resolve_session(session_id)
        if session is None:
            return
        session.cancel()
        self._finish_session(session.session_id)
        self.refresh_from_selection()

    def render_packet(self) -> GizmoRenderPacket:
        """Return renderer-facing metadata for current gizmo state."""

        return self.renderer.packet(
            self.state,
            screen_size=self.settings.normalized_size(),
            anti_aliasing=self.settings.anti_aliasing,
        )

    def set_orientation(self, mode: str) -> None:
        """Set gizmo orientation mode."""

        self.state.orientation.set_mode(mode)
        self.events.emit("GizmoOrientationChanged", "", {"mode": mode})

    def set_pivot_mode(self, mode: str) -> None:
        """Set gizmo pivot mode."""

        self.state.orientation.set_pivot_mode(mode)
        self.refresh_from_selection()
        self.events.emit("GizmoPivotModeChanged", "", {"mode": mode})

    def request_ai_gizmo(
        self,
        gizmo_type: GizmoType | str,
        *,
        target_ids: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an AI gizmo request without manipulating geometry."""

        resolved = _gizmo_type(gizmo_type)
        request = {
            "gizmo_type": resolved.value,
            "target_ids": tuple(target_ids),
            "metadata": dict(metadata or {}),
        }
        self._ai_requests.append(request)
        self.events.emit("GizmoAIRequestRecorded", "", request)
        return request

    def ai_requests(self) -> tuple[dict[str, Any], ...]:
        """Return recorded AI gizmo requests."""

        return tuple(dict(request) for request in self._ai_requests)

    def _resolve_session(self, session_id: str | None) -> GizmoSession | None:
        """Return a session by id or the active session."""

        if session_id is not None:
            return self._sessions.get(str(session_id))
        if self._active_session_id is None:
            return None
        return self._sessions.get(self._active_session_id)

    def _finish_session(self, session_id: str) -> None:
        """Remove a finished gizmo session."""

        self._sessions.pop(str(session_id), None)
        if self._active_session_id == session_id:
            self._active_session_id = None

    def _require_context(self) -> GizmoContext:
        """Return attached context or raise."""

        if self._context is None:
            raise RuntimeError("GizmoManager requires an attached GizmoContext.")
        return self._context

    def _origin_for_selection(self, selected: tuple[Any, ...]) -> Vector3:
        """Return pivot origin from selected entities."""

        centers: list[Vector3] = []
        for entity in selected:
            box = getattr(entity, "bounding_box3d", None)
            if box is not None and getattr(box, "valid", False):
                centers.append(box.center)
                continue
            position = getattr(entity, "position", None)
            if position is not None:
                centers.append(_vector3(position))
                continue
            position3d = getattr(entity, "position3d", None)
            if position3d is not None:
                centers.append(_vector3(position3d))
        if not centers:
            return self.state.origin.copy()
        total = Vector3()
        for center in centers:
            total = total + center
        return total / len(centers)


def _vector3(value: Any) -> Vector3:
    """Normalize vector-like input to Vector3."""

    if isinstance(value, Vector3):
        return value.copy()
    return Vector3(
        getattr(value, "x", 0.0),
        getattr(value, "y", 0.0),
        getattr(value, "z", 0.0),
    )
