from __future__ import annotations

from dataclasses import dataclass, field

from engine.geometry import Vector3


@dataclass
class SnappingPlane:
    """Reference plane used by snap projection workflows."""

    origin: Vector3 = field(default_factory=Vector3)
    normal: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 1.0))
    x_axis: Vector3 = field(default_factory=lambda: Vector3(1.0, 0.0, 0.0))
    y_axis: Vector3 = field(default_factory=lambda: Vector3(0.0, 1.0, 0.0))
    name: str = "World XY"

    def project(self, point: Vector3) -> Vector3:
        """Project a point onto the plane."""

        normal = self.normal.normalized()
        offset = point - self.origin
        return point - normal * offset.dot(normal)
