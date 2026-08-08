from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry.matrix4 import Matrix4
from engine.geometry.vector3 import Vector3
from engine.transform.transform_axis import TransformAxis
from engine.transform.transform_plane import TransformPlane
from engine.transform.transform_space import TransformSpace


@dataclass
class TransformState:
    """Serializable transform state for preview and future commands."""

    space: TransformSpace = TransformSpace.WORLD
    axis: TransformAxis = TransformAxis.CUSTOM
    plane: TransformPlane = TransformPlane.CUSTOM
    pivot: Vector3 = field(default_factory=Vector3)
    origin: Vector3 = field(default_factory=Vector3)
    selection_center: Vector3 = field(default_factory=Vector3)
    object_origin: Vector3 = field(default_factory=Vector3)
    feature_origin: Vector3 = field(default_factory=Vector3)
    component_origin: Vector3 = field(default_factory=Vector3)
    reference_axis: Vector3 = field(default_factory=lambda: Vector3(1.0, 0.0, 0.0))
    reference_normal: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 1.0))
    incremental_matrix: Matrix4 = field(default_factory=Matrix4.identity)
    absolute_matrix: Matrix4 = field(default_factory=Matrix4.identity)
    preview_matrix: Matrix4 = field(default_factory=Matrix4.identity)
    preview_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def enable_preview(self, matrix: Matrix4) -> None:
        """Set the current preview matrix."""

        self.preview_matrix = matrix.copy()
        self.preview_enabled = True

    def clear_preview(self) -> None:
        """Clear preview transform state."""

        self.preview_matrix = Matrix4.identity()
        self.preview_enabled = False

    def set_incremental(self, matrix: Matrix4) -> None:
        """Set the incremental transform matrix."""

        self.incremental_matrix = matrix.copy()

    def set_absolute(self, matrix: Matrix4) -> None:
        """Set the absolute transform matrix."""

        self.absolute_matrix = matrix.copy()
