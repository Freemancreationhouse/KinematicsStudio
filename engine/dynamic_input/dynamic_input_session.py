from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from engine.geometry import Vector3

from engine.dynamic_input.dynamic_input_context import DynamicInputContext
from engine.dynamic_input.dynamic_input_events import DynamicInputEvents
from engine.dynamic_input.dynamic_input_fields import (
    DynamicInputField,
    DynamicInputFieldType,
    field_type,
    make_field,
)
from engine.dynamic_input.dynamic_input_parser import DynamicInputParser
from engine.dynamic_input.dynamic_input_state import DynamicInputState


@dataclass
class DynamicInputSession:
    """Lifecycle for one active dynamic input HUD interaction."""

    context: DynamicInputContext
    parser: DynamicInputParser
    events: DynamicInputEvents
    session_id: str = field(default_factory=lambda: str(uuid4()))
    state: DynamicInputState = field(default_factory=DynamicInputState)

    def __post_init__(self) -> None:
        """Initialize state from session context."""

        self.state.viewport_id = self.context.viewport_id
        self.state.coordinate_space = self.context.coordinate_space
        self.state.units = self.context.units
        self.state.metadata.update(
            {
                "tool_name": self.context.tool_name,
                "command_name": self.context.command_name,
                "actor": self.context.actor,
            }
        )
        self.state.metadata.update(self.context.metadata)

    def add_field(self, field: DynamicInputField | DynamicInputFieldType | str) -> None:
        """Add one dynamic input field to the session."""

        resolved = field if isinstance(field, DynamicInputField) else make_field(field)
        self.state.fields[resolved.field_id] = resolved
        if not self.state.active_field_id and resolved.editable:
            self.state.set_active_field(resolved.field_id)
        self.events.emit(
            "DynamicInputFieldAdded",
            self.session_id,
            {"field_id": resolved.field_id},
        )

    def show_fields(
        self,
        fields: tuple[DynamicInputField | DynamicInputFieldType | str, ...]
        | list[DynamicInputField | DynamicInputFieldType | str],
    ) -> None:
        """Replace the session fields with a tool-specific field set."""

        self.state.fields.clear()
        self.state.active_field_id = ""
        for field in fields:
            self.add_field(field)
        self.show()
        self.events.emit(
            "DynamicInputFieldsChanged",
            self.session_id,
            {"fields": tuple(self.state.fields)},
        )

    def show(self) -> None:
        """Show the HUD for this session."""

        self.state.visible = True
        self.state.cancelled = False
        self.events.emit("DynamicInputShown", self.session_id, {})

    def hide(self) -> None:
        """Hide the HUD for this session."""

        self.state.visible = False
        self.events.emit("DynamicInputHidden", self.session_id, {})

    def update_cursor(self, position: Any) -> None:
        """Update cursor position metadata for the HUD."""

        self.state.cursor_position = _vector3(position)
        self.events.emit(
            "DynamicInputCursorMoved",
            self.session_id,
            {"position": self.state.cursor_position},
        )

    def activate_field(self, field_id: str | DynamicInputFieldType) -> DynamicInputField | None:
        """Activate one editable field."""

        resolved = str(field_id)
        if resolved not in self.state.fields:
            resolved = field_type(field_id).value
        field = self.state.set_active_field(resolved)
        self.events.emit(
            "DynamicInputFieldActivated",
            self.session_id,
            {"field_id": field.field_id if field else ""},
        )
        return field

    def tab_next(self) -> DynamicInputField | None:
        """Move keyboard focus to the next editable HUD field."""

        field = self.state.next_field()
        self.events.emit(
            "DynamicInputFieldActivated",
            self.session_id,
            {"field_id": field.field_id if field else ""},
        )
        return field

    def tab_previous(self) -> DynamicInputField | None:
        """Move keyboard focus to the previous editable HUD field."""

        field = self.state.previous_field()
        self.events.emit(
            "DynamicInputFieldActivated",
            self.session_id,
            {"field_id": field.field_id if field else ""},
        )
        return field

    def input_text(self, text: str, field_id: str | None = None) -> Any:
        """Parse user input and update the active field."""

        field = self._field_for_input(field_id)
        if field is None:
            raise RuntimeError("No dynamic input field is active.")

        parsed = self.parser.parse_field(field, text)
        self.events.emit(
            "DynamicInputValueChanged",
            self.session_id,
            {"field_id": field.field_id, "value": parsed.value, "unit": parsed.unit},
        )
        return parsed.value

    def nudge_active(self, amount: float) -> Any:
        """Increment the active field value for arrow-key interaction."""

        field = self.state.active_field()
        if field is None or not field.editable:
            return None
        current = field.value if isinstance(field.value, (int, float)) else 0.0
        field.set_value(current + float(amount), unit=field.unit)
        self.events.emit(
            "DynamicInputValueChanged",
            self.session_id,
            {"field_id": field.field_id, "value": field.value, "unit": field.unit},
        )
        return field.value

    def commit_field(self, field_id: str | None = None) -> None:
        """Commit one field value."""

        field = self._field_for_input(field_id)
        if field is None:
            return
        field.commit()
        self.events.emit(
            "DynamicInputFieldCommitted",
            self.session_id,
            {"field_id": field.field_id, "value": field.value},
        )

    def commit(self) -> dict[str, Any]:
        """Commit the session and return parsed field values."""

        for field in self.state.fields.values():
            field.commit()
        self.state.committed = True
        self.state.cancelled = False
        self.events.emit(
            "DynamicInputCommitted",
            self.session_id,
            {"values": self.state.values()},
        )
        return self.state.values()

    def cancel(self) -> None:
        """Cancel this input session."""

        self.state.cancelled = True
        self.state.committed = False
        self.hide()
        self.events.emit("DynamicInputCancelled", self.session_id, {})

    def handle_key(self, key: str, *, shift: bool = False) -> bool:
        """Handle common HUD keyboard navigation commands."""

        normalized = str(key).strip().lower()
        if normalized == "tab":
            self.tab_previous() if shift else self.tab_next()
            return True
        if normalized in {"enter", "return"}:
            self.commit()
            return True
        if normalized in {"esc", "escape"}:
            self.cancel()
            return True
        if normalized in {"up", "arrowup"}:
            self.nudge_active(1.0)
            return True
        if normalized in {"down", "arrowdown"}:
            self.nudge_active(-1.0)
            return True
        return False

    def _field_for_input(self, field_id: str | None) -> DynamicInputField | None:
        """Resolve the field receiving input."""

        if field_id is not None:
            return self.state.fields.get(str(field_id))
        return self.state.active_field()


def _vector3(value: Any) -> Vector3:
    """Convert common cursor position values to Vector3."""

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
