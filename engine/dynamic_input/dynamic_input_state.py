from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.geometry import Vector3

from engine.dynamic_input.dynamic_input_fields import DynamicInputField


@dataclass
class DynamicInputState:
    """Mutable state for one dynamic input session."""

    viewport_id: str = ""
    cursor_position: Vector3 = field(default_factory=Vector3)
    coordinate_space: str = "World"
    snap_target: str = ""
    units: str = "mm"
    visible: bool = False
    committed: bool = False
    cancelled: bool = False
    active_field_id: str = ""
    fields: dict[str, DynamicInputField] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def active_field(self) -> DynamicInputField | None:
        """Return the currently active editable field."""

        if not self.active_field_id:
            return None
        return self.fields.get(self.active_field_id)

    def editable_fields(self) -> tuple[DynamicInputField, ...]:
        """Return visible editable fields in display order."""

        return tuple(
            field
            for field in self.fields.values()
            if field.visible and field.enabled and field.editable
        )

    def set_active_field(self, field_id: str) -> DynamicInputField | None:
        """Activate one field by identifier."""

        for field in self.fields.values():
            field.active = False

        field = self.fields.get(str(field_id))
        if field is None or not field.enabled or not field.visible:
            self.active_field_id = ""
            return None

        field.active = True
        self.active_field_id = field.field_id
        return field

    def next_field(self) -> DynamicInputField | None:
        """Activate and return the next editable field."""

        fields = self.editable_fields()
        if not fields:
            return None
        if not self.active_field_id:
            return self.set_active_field(fields[0].field_id)

        ids = [field.field_id for field in fields]
        try:
            index = ids.index(self.active_field_id)
        except ValueError:
            index = -1
        return self.set_active_field(ids[(index + 1) % len(ids)])

    def previous_field(self) -> DynamicInputField | None:
        """Activate and return the previous editable field."""

        fields = self.editable_fields()
        if not fields:
            return None
        if not self.active_field_id:
            return self.set_active_field(fields[-1].field_id)

        ids = [field.field_id for field in fields]
        try:
            index = ids.index(self.active_field_id)
        except ValueError:
            index = 0
        return self.set_active_field(ids[(index - 1) % len(ids)])

    def values(self) -> dict[str, Any]:
        """Return parsed values for all fields."""

        return {field_id: field.value for field_id, field in self.fields.items()}
