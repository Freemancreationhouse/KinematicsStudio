from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import Vector2, Vector3
from engine.transform import TransformSpace, TransformState


@dataclass
class MoveContext:
    """Current move state shared by tool, session and numeric input."""

    workspace: Any
    start: Vector3
    state: TransformState = field(default_factory=TransformState)
    pivot: Vector3 = field(default_factory=Vector3)
    coordinate_system: TransformSpace = TransformSpace.WORLD
    numeric_input: dict[str, Any] = field(default_factory=dict)

    def update_delta(self, delta: Vector3) -> None:
        """Store the current move delta in transform state metadata."""

        self.state.metadata["delta"] = vector3(delta)


def point_to_vector3(point: Any) -> Vector3:
    """Convert point-like input into Vector3."""

    if isinstance(point, Vector3):
        return point.copy()
    if isinstance(point, Vector2):
        return Vector3(point.x, point.y, 0.0)
    return Vector3(
        getattr(point, "x", 0.0),
        getattr(point, "y", 0.0),
        getattr(point, "z", 0.0),
    )


def vector3(value: Any) -> Vector3:
    """Normalize vector-like input to Vector3."""

    if isinstance(value, Vector3):
        return value.copy()
    return Vector3(
        getattr(value, "x", 0.0),
        getattr(value, "y", 0.0),
        getattr(value, "z", 0.0),
    )


def vector_to_data(vector: Vector3) -> dict[str, float]:
    """Return JSON-safe vector data."""

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def delta_changed(delta: Vector3) -> bool:
    """Return True when a delta is meaningfully non-zero."""

    return (
        abs(delta.x) > 1e-9
        or abs(delta.y) > 1e-9
        or abs(delta.z) > 1e-9
    )


def translation_matrix(delta: Vector3) -> Any:
    """Return a translation matrix from the existing geometry layer."""

    from engine.geometry.matrix4 import Matrix4

    return Matrix4.translation(delta)
