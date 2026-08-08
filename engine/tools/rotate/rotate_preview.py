from __future__ import annotations

from typing import Any

from engine.geometry import Vector3

from engine.tools.rotate.rotate_command import (
    capture_entity_state,
    restore_entity_state,
    rotate_entity,
    rotated_replacements,
)
from engine.tools.rotate.rotate_context import angle_changed, axis_vector


class RotatePreview:
    """Reversible rotate preview that does not commit feature history."""

    def __init__(
        self,
        entities: list[Any],
        pivot: Vector3,
        axis: Any | None = None,
    ) -> None:
        """Create preview state for selected entities."""

        self.entities = list(entities)
        self.pivot = pivot.copy()
        self.axis = axis_vector(axis)
        self._original = {
            id(entity): capture_entity_state(entity)
            for entity in self.entities
        }
        self.angle_degrees = 0.0
        self.preview_entities: list[Any] = []

    def update(self, angle_degrees: float) -> None:
        """Apply a fresh preview angle from the original entity states."""

        self.clear()
        if not angle_changed(angle_degrees):
            self.angle_degrees = 0.0
            return
        for entity in self.entities:
            replacements = rotated_replacements(entity, self.pivot, angle_degrees)
            if replacements:
                self.preview_entities.extend(replacements)
            else:
                rotate_entity(entity, angle_degrees, self.pivot, self.axis)
        self.angle_degrees = float(angle_degrees)

    def clear(self) -> None:
        """Restore original entity state."""

        for entity in self.entities:
            state = self._original.get(id(entity))
            if state is not None:
                restore_entity_state(entity, state)
        self.preview_entities.clear()
        self.angle_degrees = 0.0

    def draw(self, painter: Any) -> None:
        """Draw replacement preview entities when available."""

        for entity in self.preview_entities:
            draw = getattr(entity, "draw", None)
            if not callable(draw):
                continue
            previous = getattr(entity, "selected", False)
            entity.selected = True
            draw(painter)
            entity.selected = previous
