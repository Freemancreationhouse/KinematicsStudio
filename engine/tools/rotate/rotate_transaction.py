from __future__ import annotations

from engine.geometry import Vector3
from engine.transform import TransformTransaction

from engine.tools.rotate.rotate_context import axis_vector, vector3


class RotateTransaction(TransformTransaction):
    """Rotate-specific transform transaction metadata."""

    @property
    def angle_degrees(self) -> float:
        """Return the transaction rotation angle in degrees."""

        return float(self.state.metadata.get("angle_degrees", 0.0))

    @property
    def pivot(self) -> Vector3:
        """Return the transaction pivot."""

        return vector3(self.state.metadata.get("pivot", Vector3()))

    @property
    def axis(self) -> Vector3:
        """Return the transaction axis."""

        return axis_vector(self.state.metadata.get("axis", Vector3(0.0, 0.0, 1.0)))
