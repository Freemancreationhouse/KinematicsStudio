from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.gizmo.gizmo_handles import GizmoAxis, GizmoHandle, GizmoPlane


@dataclass
class GizmoConstraints:
    """Active transform constraints selected by gizmo handles."""

    axis: GizmoAxis | None = None
    plane: GizmoPlane | None = None
    screen_space: bool = False
    free_rotation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def apply_handle(self, handle: GizmoHandle | None) -> None:
        """Configure constraints from an active handle."""

        self.clear()
        if handle is None:
            return
        if handle.axis is not None:
            self.axis = handle.axis
            self.screen_space = handle.axis == GizmoAxis.SCREEN
            self.free_rotation = handle.axis == GizmoAxis.FREE
        if handle.plane is not None:
            self.plane = handle.plane

    def clear(self) -> None:
        """Clear all active constraints."""

        self.axis = None
        self.plane = None
        self.screen_space = False
        self.free_rotation = False
        self.metadata.clear()

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe constraint metadata."""

        return {
            "axis": self.axis.value if self.axis else "",
            "plane": self.plane.value if self.plane else "",
            "screen_space": self.screen_space,
            "free_rotation": self.free_rotation,
            "metadata": dict(self.metadata),
        }
