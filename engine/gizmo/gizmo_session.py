from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.geometry import Vector3

from engine.gizmo.gizmo_context import GizmoContext
from engine.gizmo.gizmo_events import GizmoEvents
from engine.gizmo.gizmo_handles import GizmoHandleKind
from engine.gizmo.gizmo_state import GizmoState


@dataclass
class GizmoSession:
    """One active transform gizmo interaction session."""

    context: GizmoContext
    state: GizmoState
    events: GizmoEvents
    session_id: str = field(default_factory=lambda: str(uuid4()))
    start_point: Vector3 = field(default_factory=Vector3)
    current_point: Vector3 = field(default_factory=Vector3)
    active: bool = True

    def begin_drag(self, handle_id: str, point: Any) -> None:
        """Begin dragging one gizmo handle."""

        handle = self.state.set_active(handle_id)
        self.start_point = _vector3(point)
        self.current_point = self.start_point.copy()
        self.state.dragging = handle is not None
        self.events.emit(
            "GizmoDragStarted",
            self.session_id,
            {"handle_id": handle_id, "point": self.start_point},
        )

    def update_drag(self, point: Any) -> None:
        """Update drag state and delegate preview to existing systems."""

        if not self.active or not self.state.dragging:
            return
        resolved = self._snap_point(_vector3(point))
        self.current_point = resolved
        delta = resolved - self.start_point
        self._update_dynamic_input(delta)
        self._delegate_preview(delta)
        self.events.emit(
            "GizmoDragUpdated",
            self.session_id,
            {"delta": delta, "handle_id": self.state.active_handle_id},
        )

    def commit(self) -> Any:
        """Commit through the delegated tool or command path."""

        result = self._delegate_commit()
        self.state.clear_interaction()
        self.active = False
        self.events.emit("GizmoCommitted", self.session_id, {})
        self.events.emit("GizmoFinished", self.session_id, {})
        return result

    def cancel(self) -> None:
        """Cancel delegated preview and clear gizmo interaction state."""

        for tool in (
            self.context.move_tool,
            self.context.rotate_tool,
            self.context.scale_tool,
            self.context.copy_tool,
        ):
            cancel = getattr(tool, "cancel", None)
            if callable(cancel):
                cancel()
        self.state.clear_interaction()
        self.active = False
        self.events.emit("GizmoCancelled", self.session_id, {})
        self.events.emit("GizmoFinished", self.session_id, {})

    def _delegate_preview(self, delta: Vector3) -> None:
        """Delegate preview updates to existing editing tools."""

        handle = self.state.handles.get(self.state.active_handle_id)
        if handle is None:
            return
        if handle.kind in {
            GizmoHandleKind.MOVE_AXIS,
            GizmoHandleKind.MOVE_PLANE,
            GizmoHandleKind.MOVE_CENTER,
        }:
            self._set_tool_numeric(self.context.move_tool, delta_x=delta.x, delta_y=delta.y, delta_z=delta.z)
        elif handle.kind == GizmoHandleKind.ROTATE_RING:
            angle = delta.length()
            self._set_tool_numeric(self.context.rotate_tool, degrees=angle)
        elif handle.kind in {
            GizmoHandleKind.SCALE_AXIS,
            GizmoHandleKind.SCALE_PLANE,
            GizmoHandleKind.SCALE_UNIFORM,
        }:
            scale = 1.0 + delta.length() / 100.0
            self._set_tool_numeric(self.context.scale_tool, scale=scale, uniform_scale=scale)

    def _delegate_commit(self) -> Any:
        """Commit through the currently active delegated tool."""

        handle = self.state.handles.get(self.state.active_handle_id)
        if handle is None:
            return None
        tool = None
        if handle.kind in {
            GizmoHandleKind.MOVE_AXIS,
            GizmoHandleKind.MOVE_PLANE,
            GizmoHandleKind.MOVE_CENTER,
        }:
            tool = self.context.move_tool
        elif handle.kind == GizmoHandleKind.ROTATE_RING:
            tool = self.context.rotate_tool
        elif handle.kind in {
            GizmoHandleKind.SCALE_AXIS,
            GizmoHandleKind.SCALE_PLANE,
            GizmoHandleKind.SCALE_UNIFORM,
        }:
            tool = self.context.scale_tool
        accept = getattr(tool, "accept", None)
        return accept() if callable(accept) else None

    def _set_tool_numeric(self, tool: Any, **values: Any) -> None:
        """Update an existing tool through its public numeric-input API."""

        set_numeric_input = getattr(tool, "set_numeric_input", None)
        if callable(set_numeric_input):
            set_numeric_input(self.context.workspace, **values)

    def _update_dynamic_input(self, delta: Vector3) -> None:
        """Update the shared Dynamic Input HUD when available."""

        manager = self.context.dynamic_input_manager
        if manager is None:
            return
        try:
            session = manager.active_session()
            if session is None:
                manager.start_session(
                    workspace=self.context.workspace,
                    tool_name="TransformGizmo",
                    command_name=self.state.gizmo_type.value,
                    viewport_id=self.context.viewport_id,
                )
            manager.update_cursor(self.current_point)
        except (AttributeError, RuntimeError, ValueError):
            return

    def _snap_point(self, point: Vector3) -> Vector3:
        """Resolve cursor point through the shared Snapping Engine."""

        manager = self.context.snapping_manager
        if manager is None:
            return point
        try:
            result = manager.snap(point, self.context.workspace)
        except (AttributeError, TypeError, ValueError):
            return point
        return _vector3(getattr(result, "point", point))


def _vector3(value: Any) -> Vector3:
    """Normalize vector-like input to Vector3."""

    if isinstance(value, Vector3):
        return value.copy()
    return Vector3(
        getattr(value, "x", 0.0),
        getattr(value, "y", 0.0),
        getattr(value, "z", 0.0),
    )
