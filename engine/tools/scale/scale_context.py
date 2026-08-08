from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import Vector2, Vector3
from engine.geometry.matrix4 import Matrix4
from engine.transform import (
    TransformAxis,
    TransformPlane,
    TransformSpace,
    TransformState,
)


@dataclass
class ScaleContext:
    """Current scale state shared by tool, session and numeric input."""

    workspace: Any
    pivot: Vector3 = field(default_factory=Vector3)
    factors: Vector3 = field(default_factory=lambda: Vector3(1.0, 1.0, 1.0))
    state: TransformState = field(default_factory=TransformState)
    coordinate_system: TransformSpace = TransformSpace.WORLD
    axis_mode: TransformAxis = TransformAxis.CUSTOM
    reference_plane: TransformPlane = TransformPlane.XY
    numeric_input: dict[str, Any] = field(default_factory=dict)

    def update_factors(self, factors: Vector3) -> None:
        """Store the current scale factors in transform state metadata."""

        self.factors = scale_vector(factors)
        self.state.metadata["factors"] = self.factors
        self.state.pivot = self.pivot.copy()


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


def scale_vector(value: Any) -> Vector3:
    """Normalize factor-like input to Vector3."""

    if isinstance(value, Vector3):
        return value.copy()
    if isinstance(value, (int, float)):
        factor = float(value)
        return Vector3(factor, factor, factor)
    return Vector3(
        getattr(value, "x", 1.0),
        getattr(value, "y", 1.0),
        getattr(value, "z", 1.0),
    )


def vector_to_data(vector: Vector3) -> dict[str, float]:
    """Return JSON-safe vector data."""

    return {"x": vector.x, "y": vector.y, "z": vector.z}


def scale_changed(factors: Vector3) -> bool:
    """Return True when scale factors differ meaningfully from identity."""

    return (
        abs(factors.x - 1.0) > 1e-9
        or abs(factors.y - 1.0) > 1e-9
        or abs(factors.z - 1.0) > 1e-9
    )


def constrain_scale(factors: Any, mode: str | None = None) -> Vector3:
    """Return scale factors constrained to a supported scale mode."""

    value = scale_vector(factors)
    mode_text = str(mode or "").upper()
    if mode_text == "X":
        return Vector3(value.x, 1.0, 1.0)
    if mode_text == "Y":
        return Vector3(1.0, value.y, 1.0)
    if mode_text == "Z":
        return Vector3(1.0, 1.0, value.z)
    if mode_text == "XY":
        return Vector3(value.x, value.y, 1.0)
    if mode_text == "XZ":
        return Vector3(value.x, 1.0, value.z)
    if mode_text == "YZ":
        return Vector3(1.0, value.y, value.z)
    return value


def scale_matrix(factors: Any, pivot: Vector3 | None = None) -> Matrix4:
    """Return a scale matrix around an optional pivot."""

    matrix = Matrix4.scaling(scale_vector(factors))
    if pivot is None:
        return matrix
    return Matrix4.around_pivot(matrix, point_to_vector3(pivot))


def scale_point_2d(point: Any, pivot: Any, factors: Any) -> Vector2:
    """Scale a 2D point around a pivot in the XY plane."""

    source = point_to_vector3(point)
    center = point_to_vector3(pivot)
    scale = scale_vector(factors)
    return Vector2(
        center.x + (source.x - center.x) * scale.x,
        center.y + (source.y - center.y) * scale.y,
    )


def scale_point_3d(point: Any, pivot: Any, factors: Any) -> Vector3:
    """Scale a 3D point around a pivot."""

    source = point_to_vector3(point)
    center = point_to_vector3(pivot)
    scale = scale_vector(factors)
    return Vector3(
        center.x + (source.x - center.x) * scale.x,
        center.y + (source.y - center.y) * scale.y,
        center.z + (source.z - center.z) * scale.z,
    )
