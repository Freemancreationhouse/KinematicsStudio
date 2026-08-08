from __future__ import annotations

from dataclasses import dataclass, field

from engine.geometry import Vector3
from engine.snapping.snapping_result import SnappingResult


@dataclass(frozen=True)
class SnappingMarker:
    """Visual feedback metadata for the rendering pipeline."""

    point: Vector3
    mode: str
    label: str = ""
    highlight: bool = True
    cursor_indicator: bool = True
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_result(cls, result: SnappingResult) -> "SnappingMarker | None":
        """Create marker metadata from an active snapping result."""

        if not result.active:
            return None
        return cls(
            point=result.point.copy(),
            mode=result.mode,
            label=result.label,
            metadata=dict(result.metadata),
        )
