from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from engine.snapping.snapping_target import SnappingTargetType


class SnappingMode(str, Enum):
    """Supported snapping operation modes."""

    SINGLE = "Single Snap"
    MULTI = "Multi Snap"
    TEMPORARY_OVERRIDE = "Temporary Override"
    PERSISTENT = "Persistent Snap"
    SMART = "Smart Snap"


@dataclass
class SnappingSettings:
    """Serializable snapping settings."""

    enabled: bool = True
    mode: SnappingMode = SnappingMode.SMART
    tolerance: float = 12.0
    grid_spacing: float = 25.0
    enabled_targets: set[SnappingTargetType] = field(
        default_factory=lambda: set(SnappingTargetType)
    )
    snap_to_grid: bool = True
    snap_to_origin: bool = True
    hover_marker: bool = True
    snap_marker: bool = True
    highlight: bool = True
    preview_marker: bool = True
    snap_label: bool = True
    cursor_indicator: bool = True

    def to_dict(self) -> dict[str, object]:
        """Return JSON-safe settings."""

        return {
            "enabled": self.enabled,
            "mode": self.mode.value,
            "tolerance": self.tolerance,
            "grid_spacing": self.grid_spacing,
            "enabled_targets": sorted(target.value for target in self.enabled_targets),
            "snap_to_grid": self.snap_to_grid,
            "snap_to_origin": self.snap_to_origin,
            "hover_marker": self.hover_marker,
            "snap_marker": self.snap_marker,
            "highlight": self.highlight,
            "preview_marker": self.preview_marker,
            "snap_label": self.snap_label,
            "cursor_indicator": self.cursor_indicator,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> "SnappingSettings":
        """Create settings from JSON-safe data."""

        data = data or {}
        settings = cls()
        settings.enabled = bool(data.get("enabled", settings.enabled))
        settings.mode = _mode(data.get("mode", settings.mode.value))
        settings.tolerance = float(data.get("tolerance", settings.tolerance))
        settings.grid_spacing = float(data.get("grid_spacing", settings.grid_spacing))
        settings.enabled_targets = {
            _target_type(item)
            for item in data.get("enabled_targets", [])
        } or set(SnappingTargetType)
        settings.snap_to_grid = bool(data.get("snap_to_grid", settings.snap_to_grid))
        settings.snap_to_origin = bool(data.get("snap_to_origin", settings.snap_to_origin))
        return settings


def _mode(value: object) -> SnappingMode:
    """Normalize snapping mode values."""

    text = str(value)
    for mode in SnappingMode:
        if text.upper() in (mode.name.upper(), mode.value.upper()):
            return mode
    return SnappingMode.SMART


def _target_type(value: object) -> SnappingTargetType:
    """Normalize snapping target values."""

    text = str(value)
    for target_type in SnappingTargetType:
        if text.upper() in (target_type.name.upper(), target_type.value.upper()):
            return target_type
    return SnappingTargetType.NEAREST
