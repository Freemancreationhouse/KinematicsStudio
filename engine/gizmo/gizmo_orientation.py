from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engine.geometry import Vector3


class GizmoOrientationMode(str, Enum):
    """Supported gizmo orientation modes."""

    WORLD = "world"
    LOCAL = "local"
    PARENT = "parent"
    VIEW = "view"
    CUSTOM = "custom"


class GizmoPivotMode(str, Enum):
    """Supported gizmo pivot modes."""

    SELECTION_CENTER = "selection_center"
    BOUNDING_BOX_CENTER = "bounding_box_center"
    ORIGIN = "origin"
    CUSTOM_PIVOT = "custom_pivot"
    ACTIVE_PIVOT = "active_pivot"


@dataclass
class GizmoOrientation:
    """Orientation and pivot description for a transform gizmo."""

    mode: GizmoOrientationMode = GizmoOrientationMode.WORLD
    pivot_mode: GizmoPivotMode = GizmoPivotMode.SELECTION_CENTER
    pivot: Vector3 = field(default_factory=Vector3)
    x_axis: Vector3 = field(default_factory=lambda: Vector3(1.0, 0.0, 0.0))
    y_axis: Vector3 = field(default_factory=lambda: Vector3(0.0, 1.0, 0.0))
    z_axis: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 1.0))
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_mode(self, mode: GizmoOrientationMode | str) -> None:
        """Set orientation mode."""

        self.mode = _orientation_mode(mode)

    def set_pivot_mode(self, mode: GizmoPivotMode | str) -> None:
        """Set pivot mode."""

        self.pivot_mode = _pivot_mode(mode)

    def set_pivot(self, pivot: Any) -> None:
        """Set the active pivot point."""

        self.pivot = _vector3(pivot)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe orientation metadata."""

        return {
            "mode": self.mode.value,
            "pivot_mode": self.pivot_mode.value,
            "pivot": self.pivot.to_tuple(),
            "x_axis": self.x_axis.to_tuple(),
            "y_axis": self.y_axis.to_tuple(),
            "z_axis": self.z_axis.to_tuple(),
            "metadata": dict(self.metadata),
        }


def _orientation_mode(value: GizmoOrientationMode | str) -> GizmoOrientationMode:
    """Return orientation mode from enum or string."""

    if isinstance(value, GizmoOrientationMode):
        return value
    return GizmoOrientationMode(str(value).strip().lower())


def _pivot_mode(value: GizmoPivotMode | str) -> GizmoPivotMode:
    """Return pivot mode from enum or string."""

    if isinstance(value, GizmoPivotMode):
        return value
    return GizmoPivotMode(str(value).strip().lower())


def _vector3(value: Any) -> Vector3:
    """Normalize vector-like input to Vector3."""

    if isinstance(value, Vector3):
        return value.copy()
    return Vector3(
        getattr(value, "x", 0.0),
        getattr(value, "y", 0.0),
        getattr(value, "z", 0.0),
    )
