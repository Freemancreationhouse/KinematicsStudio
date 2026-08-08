from __future__ import annotations

from dataclasses import dataclass

from engine.geometry import Vector3


@dataclass
class SnappingGrid:
    """Grid snapping helper."""

    spacing: float = 25.0
    origin: Vector3 = Vector3()

    def snap(self, point: Vector3) -> Vector3:
        """Return the nearest grid point."""

        spacing = max(float(self.spacing), 0.0001)
        return Vector3(
            self.origin.x + round((point.x - self.origin.x) / spacing) * spacing,
            self.origin.y + round((point.y - self.origin.y) / spacing) * spacing,
            self.origin.z + round((point.z - self.origin.z) / spacing) * spacing,
        )
