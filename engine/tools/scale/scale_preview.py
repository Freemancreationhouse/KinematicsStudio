from __future__ import annotations

from typing import Any

from engine.geometry import Vector3

from engine.tools.scale.scale_command import (
    capture_entity_state,
    restore_entity_state,
    scale_entity,
    scaled_replacements,
)
from engine.tools.scale.scale_context import scale_changed, scale_vector


class ScalePreview:
    """Reversible scale preview that does not commit feature history."""

    def __init__(self, entities: list[Any], pivot: Vector3) -> None:
        """Create preview state for selected entities."""

        self.entities = list(entities)
        self.pivot = pivot.copy()
        self._original = {
            id(entity): capture_entity_state(entity)
            for entity in self.entities
        }
        self.factors = Vector3(1.0, 1.0, 1.0)
        self.preview_entities: list[Any] = []

    def update(self, factors: Vector3) -> None:
        """Apply fresh preview factors from the original entity states."""

        self.clear()
        normalized = scale_vector(factors)
        if not scale_changed(normalized):
            self.factors = Vector3(1.0, 1.0, 1.0)
            return
        for entity in self.entities:
            replacements = scaled_replacements(entity, self.pivot, normalized)
            if replacements:
                self.preview_entities.extend(replacements)
            else:
                scale_entity(entity, normalized, self.pivot)
        self.factors = normalized

    def clear(self) -> None:
        """Restore original entity state."""

        for entity in self.entities:
            state = self._original.get(id(entity))
            if state is not None:
                restore_entity_state(entity, state)
        self.preview_entities.clear()
        self.factors = Vector3(1.0, 1.0, 1.0)

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
