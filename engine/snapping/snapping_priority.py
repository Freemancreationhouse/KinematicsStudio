from __future__ import annotations

from engine.snapping.snapping_target import SnappingTargetType


class SnappingPriority:
    """Configurable priority ordering for snap target selection."""

    DEFAULT_ORDER = (
        SnappingTargetType.ENDPOINT,
        SnappingTargetType.INTERSECTION,
        SnappingTargetType.MIDPOINT,
        SnappingTargetType.CENTER,
        SnappingTargetType.QUADRANT,
        SnappingTargetType.BODY_CENTER,
        SnappingTargetType.BOUNDING_BOX_CENTER,
        SnappingTargetType.SELECTION_CENTER,
        SnappingTargetType.REFERENCE_VERTEX,
        SnappingTargetType.REFERENCE_EDGE,
        SnappingTargetType.REFERENCE_FACE,
        SnappingTargetType.NEAREST,
        SnappingTargetType.PERPENDICULAR,
        SnappingTargetType.TANGENT,
        SnappingTargetType.PARALLEL,
        SnappingTargetType.ORIGIN,
        SnappingTargetType.GRID,
        SnappingTargetType.CONSTRUCTION_POINT,
        SnappingTargetType.CONSTRUCTION_LINE,
        SnappingTargetType.CONSTRUCTION_PLANE,
        SnappingTargetType.REFERENCE_AXIS,
        SnappingTargetType.REFERENCE_PLANE,
    )

    def __init__(self, order: tuple[SnappingTargetType | str, ...] | None = None) -> None:
        """Create a priority table."""

        self._order: list[SnappingTargetType] = []
        self.set_order(order or self.DEFAULT_ORDER)

    def set_order(self, order: tuple[SnappingTargetType | str, ...]) -> None:
        """Replace the full snap priority order."""

        self._order = [_target_type(item) for item in order]

    def set_priority(self, target_type: SnappingTargetType | str, priority: int) -> None:
        """Assign a target type to a specific priority position."""

        resolved = _target_type(target_type)
        self._order = [item for item in self._order if item != resolved]
        index = max(0, min(int(priority), len(self._order)))
        self._order.insert(index, resolved)

    def priority(self, target_type: SnappingTargetType | str) -> int:
        """Return the numeric priority for a target type."""

        resolved = _target_type(target_type)
        try:
            return self._order.index(resolved)
        except ValueError:
            return 10_000

    def order(self) -> tuple[SnappingTargetType, ...]:
        """Return the configured priority order."""

        return tuple(self._order)


def _target_type(value: SnappingTargetType | str) -> SnappingTargetType:
    """Normalize snap target type values."""

    if isinstance(value, SnappingTargetType):
        return value
    text = str(value)
    for target_type in SnappingTargetType:
        if text.upper() in (target_type.name.upper(), target_type.value.upper()):
            return target_type
    return SnappingTargetType.NEAREST
