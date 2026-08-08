from __future__ import annotations

from dataclasses import dataclass, field

from engine.snapping.snapping_target import (
    SnappingTarget,
    SnappingTargetCategory,
    SnappingTargetType,
)


@dataclass
class SnappingFilter:
    """Configurable snap category and target-type filter."""

    enabled_categories: set[SnappingTargetCategory] = field(
        default_factory=lambda: set(SnappingTargetCategory)
    )
    enabled_target_types: set[SnappingTargetType] = field(
        default_factory=lambda: set(SnappingTargetType)
    )

    def allows(self, target: SnappingTarget) -> bool:
        """Return True when the target is enabled."""

        return (
            target.category in self.enabled_categories
            and target.target_type in self.enabled_target_types
        )

    def enable_category(self, category: SnappingTargetCategory | str) -> None:
        """Enable a target category."""

        self.enabled_categories.add(_category(category))

    def disable_category(self, category: SnappingTargetCategory | str) -> None:
        """Disable a target category."""

        self.enabled_categories.discard(_category(category))

    def enable_target_type(self, target_type: SnappingTargetType | str) -> None:
        """Enable a target type."""

        self.enabled_target_types.add(_target_type(target_type))

    def disable_target_type(self, target_type: SnappingTargetType | str) -> None:
        """Disable a target type."""

        self.enabled_target_types.discard(_target_type(target_type))


def _category(value: SnappingTargetCategory | str) -> SnappingTargetCategory:
    """Normalize category values."""

    if isinstance(value, SnappingTargetCategory):
        return value
    text = str(value)
    for category in SnappingTargetCategory:
        if text.upper() in (category.name.upper(), category.value.upper()):
            return category
    return SnappingTargetCategory.GEOMETRY


def _target_type(value: SnappingTargetType | str) -> SnappingTargetType:
    """Normalize target type values."""

    if isinstance(value, SnappingTargetType):
        return value
    text = str(value)
    for target_type in SnappingTargetType:
        if text.upper() in (target_type.name.upper(), target_type.value.upper()):
            return target_type
    return SnappingTargetType.NEAREST
