from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from engine.geometry import Vector3
from engine.snapping.snapping_result import SnappingResult


@dataclass
class SnappingSession:
    """Tracks a professional snapping interaction session."""

    workspace: object
    session_id: str = field(default_factory=lambda: str(uuid4()))
    active: bool = True
    last_point: Vector3 = field(default_factory=Vector3)
    last_result: SnappingResult = field(default_factory=SnappingResult.off)
    results: list[SnappingResult] = field(default_factory=list)
    temporary_overrides: set[str] = field(default_factory=set)

    def update(self, result: SnappingResult) -> None:
        """Store the latest snapping result."""

        self.last_result = result
        self.last_point = result.point.copy()
        if result.active:
            self.results.append(result)

    def set_temporary_overrides(self, modes: set[str]) -> None:
        """Set temporary snap mode overrides for this session."""

        self.temporary_overrides = {str(mode) for mode in modes}

    def finish(self) -> None:
        """Mark this session complete."""

        self.active = False
