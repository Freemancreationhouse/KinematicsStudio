from __future__ import annotations

from engine.geometry import Vector3
from engine.transform import TransformTransaction

from engine.tools.scale.scale_context import point_to_vector3, scale_vector


class ScaleTransaction(TransformTransaction):
    """Scale-specific transform transaction metadata."""

    @property
    def factors(self) -> Vector3:
        """Return the transaction scale factors."""

        return scale_vector(self.state.metadata.get("factors", Vector3(1.0, 1.0, 1.0)))

    @property
    def pivot(self) -> Vector3:
        """Return the transaction pivot."""

        return point_to_vector3(self.state.metadata.get("pivot", Vector3()))
