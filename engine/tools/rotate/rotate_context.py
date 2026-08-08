from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians, sin
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
class RotateContext:
    """Current rotate state shared by tool, session and numeric input."""

    workspace: Any
    pivot: Vector3 = field(default_factory=Vector3)
    axis: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 1.0))
    state: TransformState = field(default_factory=TransformState)
    coordinate_system: TransformSpace = TransformSpace.WORLD
    axis_mode: TransformAxis = TransformAxis.Z
    reference_plane: TransformPlane = TransformPlane.XY
    numeric_input: dict[str, Any] = field(default_factory=dict)

    def update_angle(self, angle_degrees: float) -> None:
        """Store the current rotate angle in transform state metadata."""

        self.state.metadata["angle_degrees"] = float(angle_degrees)
        self.state.pivot = self.pivot.copy()
        self.state.reference_axis = vector3(self.axis).normalized()


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


def angle_changed(angle_degrees: float) -> bool:
    """Return True when a rotation angle is meaningfully non-zero."""

    return abs(float(angle_degrees)) > 1e-9


def axis_vector(axis: Any | None = None) -> Vector3:
    """Return a world-space axis vector for supported axis identifiers."""

    if axis is None:
        return Vector3(0.0, 0.0, 1.0)

    if isinstance(axis, Vector3):
        normalized = axis.normalized()
        return normalized if normalized.length_squared() > 0.0 else Vector3(0.0, 0.0, 1.0)

    axis_value = getattr(axis, "value", axis)
    axis_text = str(axis_value or "").upper()
    if axis_text == "X":
        return Vector3(1.0, 0.0, 0.0)
    if axis_text == "Y":
        return Vector3(0.0, 1.0, 0.0)
    return Vector3(0.0, 0.0, 1.0)


def rotation_vector(angle_degrees: float, axis: Any | None = None) -> Vector3:
    """Return Euler rotation metadata for supported primary axes."""

    axis_value = axis_vector(axis)
    if abs(axis_value.x) >= abs(axis_value.y) and abs(axis_value.x) >= abs(axis_value.z):
        return Vector3(float(angle_degrees), 0.0, 0.0)
    if abs(axis_value.y) >= abs(axis_value.x) and abs(axis_value.y) >= abs(axis_value.z):
        return Vector3(0.0, float(angle_degrees), 0.0)
    return Vector3(0.0, 0.0, float(angle_degrees))


def rotation_matrix(
    angle_degrees: float,
    pivot: Vector3 | None = None,
    axis: Any | None = None,
) -> Matrix4:
    """Return a rotation matrix around a world-space pivot."""

    direction = axis_vector(axis).normalized()
    theta = radians(float(angle_degrees))
    cosine = cos(theta)
    sine = sin(theta)
    one_minus_cosine = 1.0 - cosine
    x = direction.x
    y = direction.y
    z = direction.z
    matrix = Matrix4([
        cosine + x * x * one_minus_cosine,
        x * y * one_minus_cosine - z * sine,
        x * z * one_minus_cosine + y * sine,
        0.0,
        y * x * one_minus_cosine + z * sine,
        cosine + y * y * one_minus_cosine,
        y * z * one_minus_cosine - x * sine,
        0.0,
        z * x * one_minus_cosine - y * sine,
        z * y * one_minus_cosine + x * sine,
        cosine + z * z * one_minus_cosine,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    ])
    if pivot is None:
        return matrix
    return Matrix4.around_pivot(matrix, vector3(pivot))


def rotate_point_2d(point: Any, pivot: Any, angle_degrees: float) -> Vector2:
    """Rotate a 2D point around a pivot in the XY plane."""

    source = point_to_vector3(point)
    center = point_to_vector3(pivot)
    theta = radians(float(angle_degrees))
    cosine = cos(theta)
    sine = sin(theta)
    dx = source.x - center.x
    dy = source.y - center.y
    return Vector2(
        center.x + dx * cosine - dy * sine,
        center.y + dx * sine + dy * cosine,
    )


def rotate_point_3d(
    point: Any,
    pivot: Any,
    angle_degrees: float,
    axis: Any | None = None,
) -> Vector3:
    """Rotate a point around an axis in 3D space."""

    source = point_to_vector3(point)
    center = point_to_vector3(pivot)
    direction = axis_vector(axis).normalized()
    relative = source - center
    theta = radians(float(angle_degrees))
    cosine = cos(theta)
    sine = sin(theta)
    rotated = (
        relative * cosine
        + direction.cross(relative) * sine
        + direction * (direction.dot(relative) * (1.0 - cosine))
    )
    return center + rotated
