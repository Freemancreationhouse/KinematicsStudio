from __future__ import annotations

from dataclasses import dataclass, field

from engine.transform.transform_axis import TransformAxis
from engine.transform.transform_plane import TransformPlane


@dataclass
class TransformConstraints:
    """Constraint metadata applied to a transform session."""

    axes: set[TransformAxis] = field(
        default_factory=lambda: {
            TransformAxis.X,
            TransformAxis.Y,
            TransformAxis.Z,
        }
    )
    planes: set[TransformPlane] = field(
        default_factory=lambda: {
            TransformPlane.XY,
            TransformPlane.YZ,
            TransformPlane.XZ,
        }
    )
    uniform_scale: bool = False
    preserve_orientation: bool = False
    preserve_topology: bool = True
    snap_increment: float | None = None
    min_scale: float | None = None
    max_scale: float | None = None

    def allows_axis(self, axis: TransformAxis | str) -> bool:
        """Return True when an axis is allowed by this constraint set."""

        normalized = axis if isinstance(axis, TransformAxis) else TransformAxis(str(axis))
        return normalized in self.axes or normalized == TransformAxis.CUSTOM

    def allows_plane(self, plane: TransformPlane | str) -> bool:
        """Return True when a plane is allowed by this constraint set."""

        normalized = (
            plane if isinstance(plane, TransformPlane) else TransformPlane(str(plane))
        )
        return normalized in self.planes or normalized == TransformPlane.CUSTOM

    def require_axis(self, axis: TransformAxis | str) -> None:
        """Raise ValueError if an axis is disallowed."""

        if not self.allows_axis(axis):
            raise ValueError(f"Transform axis is constrained: {axis!r}")

    def require_plane(self, plane: TransformPlane | str) -> None:
        """Raise ValueError if a plane is disallowed."""

        if not self.allows_plane(plane):
            raise ValueError(f"Transform plane is constrained: {plane!r}")
