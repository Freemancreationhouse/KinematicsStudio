from __future__ import annotations

from engine.geometry import Vector3
from engine.transform import TransformTransaction

from engine.tools.move.move_context import vector3


class MoveTransaction(TransformTransaction):
    """Move-specific transform transaction metadata."""

    @property
    def delta(self) -> Vector3:
        """Return the transaction move delta."""

        return vector3(self.state.metadata.get("delta", Vector3()))
