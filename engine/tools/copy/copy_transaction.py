from __future__ import annotations

from engine.geometry import Vector3
from engine.transform import TransformTransaction

from engine.tools.copy.copy_context import vector3


class CopyTransaction(TransformTransaction):
    """Copy-specific transform transaction metadata."""

    @property
    def delta(self) -> Vector3:
        """Return the transaction copy offset."""

        return vector3(self.state.metadata.get("delta", Vector3()))

    @property
    def copies(self) -> int:
        """Return the number of copies requested."""

        return int(self.state.metadata.get("copies", 1))
