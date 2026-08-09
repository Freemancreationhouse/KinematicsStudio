from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import Vector3

from engine.gizmo.gizmo_constraints import GizmoConstraints
from engine.gizmo.gizmo_handles import (
    GizmoHandle,
    GizmoType,
    _gizmo_type,
    standard_handles,
)
from engine.gizmo.gizmo_orientation import GizmoOrientation


@dataclass
class GizmoState:
    """Mutable state for the active transform gizmo."""

    visible: bool = False
    gizmo_type: GizmoType = GizmoType.UNIVERSAL
    origin: Vector3 = field(default_factory=Vector3)
    handles: dict[str, GizmoHandle] = field(default_factory=dict)
    hovered_handle_id: str = ""
    active_handle_id: str = ""
    orientation: GizmoOrientation = field(default_factory=GizmoOrientation)
    constraints: GizmoConstraints = field(default_factory=GizmoConstraints)
    selected_entities: tuple[Any, ...] = ()
    viewport_id: str = ""
    dragging: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def configure_handles(self, gizmo_type: GizmoType | str) -> None:
        """Install standard handles for a gizmo type."""

        self.gizmo_type = _gizmo_type(gizmo_type)
        self.handles = {
            handle.handle_id: handle for handle in standard_handles(self.gizmo_type)
        }

    def set_hovered(self, handle_id: str) -> GizmoHandle | None:
        """Set the hovered handle."""

        self.hovered_handle_id = str(handle_id or "")
        for handle in self.handles.values():
            handle.hovered = handle.handle_id == self.hovered_handle_id
        return self.handles.get(self.hovered_handle_id)

    def set_active(self, handle_id: str) -> GizmoHandle | None:
        """Set the active handle and update constraints."""

        self.active_handle_id = str(handle_id or "")
        for handle in self.handles.values():
            handle.active = handle.handle_id == self.active_handle_id
        handle = self.handles.get(self.active_handle_id)
        self.constraints.apply_handle(handle)
        return handle

    def clear_interaction(self) -> None:
        """Clear hover, active handle and drag state."""

        self.dragging = False
        self.hovered_handle_id = ""
        self.active_handle_id = ""
        for handle in self.handles.values():
            handle.hovered = False
            handle.active = False
        self.constraints.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return JSON-safe state for viewport presenters."""

        return {
            "visible": self.visible,
            "gizmo_type": self.gizmo_type.value,
            "origin": self.origin.to_tuple(),
            "hovered_handle_id": self.hovered_handle_id,
            "active_handle_id": self.active_handle_id,
            "orientation": self.orientation.to_dict(),
            "constraints": self.constraints.to_dict(),
            "selected_count": len(self.selected_entities),
            "viewport_id": self.viewport_id,
            "dragging": self.dragging,
            "handles": [handle.to_dict() for handle in self.handles.values()],
            "metadata": dict(self.metadata),
        }

    def __post_init__(self) -> None:
        """Install the default universal gizmo handles."""

        if not self.handles:
            self.configure_handles(self.gizmo_type)
