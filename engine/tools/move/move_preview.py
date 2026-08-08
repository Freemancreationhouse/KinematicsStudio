from __future__ import annotations

from typing import Any

from engine.geometry import Vector3

from engine.tools.move.move_command import move_entity
from engine.tools.move.move_context import delta_changed, vector3


class MovePreview:
    """Reversible move preview that is cleared before command commit."""

    def __init__(self, entities: list[Any]) -> None:
        """Create a move preview for entities."""

        self.entities = list(entities)
        self.delta = Vector3()
        self.active = False

    def update(self, delta: Vector3) -> None:
        """Update preview geometry to a new move delta."""

        self.clear()
        self.delta = vector3(delta)
        if not delta_changed(self.delta):
            return
        for entity in self.entities:
            move_entity(entity, self.delta)
        self.active = True

    def clear(self) -> None:
        """Clear preview geometry by applying the inverse delta."""

        if not self.active:
            return
        inverse = Vector3(-self.delta.x, -self.delta.y, -self.delta.z)
        for entity in self.entities:
            move_entity(entity, inverse)
        self.delta = Vector3()
        self.active = False
