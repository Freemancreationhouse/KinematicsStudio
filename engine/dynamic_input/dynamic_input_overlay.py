from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engine.geometry import Vector3

from engine.dynamic_input.dynamic_input_fields import DynamicInputField
from engine.dynamic_input.dynamic_input_state import DynamicInputState


class DynamicInputTheme(str, Enum):
    """Supported HUD visual theme modes."""

    DARK = "dark"
    LIGHT = "light"


@dataclass
class DynamicInputOverlay:
    """Viewport-independent cursor HUD presentation model."""

    viewport_id: str = ""
    visible: bool = False
    cursor_position: Vector3 = field(default_factory=Vector3)
    scale_factor: float = 1.0
    theme: DynamicInputTheme = DynamicInputTheme.DARK
    fields: tuple[DynamicInputField, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def show(self) -> None:
        """Mark the HUD overlay visible."""

        self.visible = True

    def hide(self) -> None:
        """Mark the HUD overlay hidden."""

        self.visible = False

    def move_to(self, position: Any) -> None:
        """Move the overlay to a cursor position."""

        self.cursor_position = _vector3(position)

    def set_scale_factor(self, scale_factor: float) -> None:
        """Set the HiDPI scale factor used by a presenter."""

        self.scale_factor = max(float(scale_factor), 0.1)

    def set_theme(self, theme: DynamicInputTheme | str) -> None:
        """Set the presentation theme metadata."""

        if isinstance(theme, DynamicInputTheme):
            self.theme = theme
        else:
            self.theme = DynamicInputTheme(str(theme).strip().lower())

    def update_from_state(self, state: DynamicInputState) -> None:
        """Synchronize overlay metadata from session state."""

        self.viewport_id = state.viewport_id
        self.visible = state.visible
        self.cursor_position = state.cursor_position.copy()
        self.fields = tuple(state.fields.values())
        self.metadata = dict(state.metadata)

    def snapshot(self) -> dict[str, Any]:
        """Return a serializable representation for a UI presenter."""

        return {
            "viewport_id": self.viewport_id,
            "visible": self.visible,
            "cursor_position": self.cursor_position.to_tuple(),
            "scale_factor": self.scale_factor,
            "theme": self.theme.value,
            "fields": [
                {
                    "id": field.field_id,
                    "type": field.field_type.value,
                    "label": field.label,
                    "value": field.value,
                    "display": field.display_value(),
                    "visible": field.visible,
                    "enabled": field.enabled,
                    "editable": field.editable,
                    "active": field.active,
                }
                for field in self.fields
            ],
            "metadata": dict(self.metadata),
        }


def _vector3(value: Any) -> Vector3:
    """Convert common cursor position inputs to Vector3."""

    if isinstance(value, Vector3):
        return value.copy()
    if hasattr(value, "x") and hasattr(value, "y"):
        return Vector3(
            float(value.x),
            float(value.y),
            float(getattr(value, "z", 0.0)),
        )
    if isinstance(value, (tuple, list)):
        x = value[0] if len(value) > 0 else 0.0
        y = value[1] if len(value) > 1 else 0.0
        z = value[2] if len(value) > 2 else 0.0
        return Vector3(x, y, z)
    return Vector3()
