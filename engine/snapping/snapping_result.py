from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import Vector3
from engine.snapping.snapping_target import SnappingTarget, SnappingTargetType


@dataclass(frozen=True)
class SnappingResult:
    """Resolved snapping result for tools, commands and visual feedback."""

    point: Vector3
    mode: str = "OFF"
    target: SnappingTarget | None = None
    entity: Any = None
    distance: float = float("inf")
    priority: int = 10_000
    label: str = ""
    active: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def off(cls, point: Vector3 | None = None) -> "SnappingResult":
        """Return an inactive snapping result."""

        return cls(point=point or Vector3(), active=False)

    @classmethod
    def from_target(
        cls,
        target: SnappingTarget,
        *,
        distance: float,
        priority: int,
    ) -> "SnappingResult":
        """Create an active result from a snap target."""

        return cls(
            point=target.point.copy(),
            mode=target.target_type.value,
            target=target,
            entity=target.source,
            distance=float(distance),
            priority=int(priority),
            label=target.label or target.target_type.value,
            active=True,
            metadata=dict(target.metadata),
        )

    @property
    def target_type(self) -> SnappingTargetType | None:
        """Return the target type when active."""

        return self.target.target_type if self.target is not None else None
