from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DynamicInputFieldType(str, Enum):
    """Supported dynamic input HUD field types."""

    DELTA_X = "delta_x"
    DELTA_Y = "delta_y"
    DELTA_Z = "delta_z"
    DISTANCE = "distance"
    ANGLE = "angle"
    SCALE = "scale"
    RADIUS = "radius"
    OFFSET = "offset"
    COPIES = "copies"
    ROWS = "rows"
    COLUMNS = "columns"
    SPACING = "spacing"
    COORDINATE_SPACE = "coordinate_space"
    SNAP_TARGET = "snap_target"
    UNITS = "units"


@dataclass
class DynamicInputField:
    """One editable or display-only field in the cursor HUD."""

    field_id: str
    field_type: DynamicInputFieldType
    label: str
    value: Any = None
    raw_text: str = ""
    unit: str = ""
    visible: bool = True
    enabled: bool = True
    editable: bool = True
    active: bool = False
    committed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_text(self, text: str) -> None:
        """Store user-entered text for this field."""

        self.raw_text = str(text)
        self.committed = False

    def set_value(self, value: Any, *, unit: str = "") -> None:
        """Store the parsed field value."""

        self.value = value
        self.unit = unit
        self.committed = False

    def commit(self) -> None:
        """Mark this field as committed."""

        self.committed = True

    def display_value(self) -> str:
        """Return the value intended for the HUD display."""

        if self.raw_text:
            return self.raw_text
        if self.value is None:
            return ""
        if isinstance(self.value, float):
            text = f"{self.value:.6g}"
        else:
            text = str(self.value)
        return f"{text}{self.unit}" if self.unit else text


def field_type(value: DynamicInputFieldType | str) -> DynamicInputFieldType:
    """Return a DynamicInputFieldType from a string or enum value."""

    if isinstance(value, DynamicInputFieldType):
        return value
    normalized = str(value).strip().lower().replace(" ", "_")
    aliases = {
        "dx": DynamicInputFieldType.DELTA_X,
        "dy": DynamicInputFieldType.DELTA_Y,
        "dz": DynamicInputFieldType.DELTA_Z,
        "deltax": DynamicInputFieldType.DELTA_X,
        "deltay": DynamicInputFieldType.DELTA_Y,
        "deltaz": DynamicInputFieldType.DELTA_Z,
    }
    return aliases.get(normalized, DynamicInputFieldType(normalized))


def make_field(value: DynamicInputFieldType | str) -> DynamicInputField:
    """Create a standard field definition for a type."""

    resolved = field_type(value)
    labels = {
        DynamicInputFieldType.DELTA_X: "ΔX",
        DynamicInputFieldType.DELTA_Y: "ΔY",
        DynamicInputFieldType.DELTA_Z: "ΔZ",
        DynamicInputFieldType.DISTANCE: "Distance",
        DynamicInputFieldType.ANGLE: "Angle",
        DynamicInputFieldType.SCALE: "Scale",
        DynamicInputFieldType.RADIUS: "Radius",
        DynamicInputFieldType.OFFSET: "Offset",
        DynamicInputFieldType.COPIES: "Copies",
        DynamicInputFieldType.ROWS: "Rows",
        DynamicInputFieldType.COLUMNS: "Columns",
        DynamicInputFieldType.SPACING: "Spacing",
        DynamicInputFieldType.COORDINATE_SPACE: "Space",
        DynamicInputFieldType.SNAP_TARGET: "Snap",
        DynamicInputFieldType.UNITS: "Units",
    }
    return DynamicInputField(
        field_id=resolved.value,
        field_type=resolved,
        label=labels[resolved],
        editable=resolved
        not in {
            DynamicInputFieldType.COORDINATE_SPACE,
            DynamicInputFieldType.SNAP_TARGET,
            DynamicInputFieldType.UNITS,
        },
    )
