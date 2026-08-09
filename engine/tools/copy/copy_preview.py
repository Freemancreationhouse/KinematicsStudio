from __future__ import annotations

from typing import Any

from engine.geometry import Vector3

from engine.tools.copy.copy_command import clone_entity
from engine.tools.copy.copy_context import delta_changed, vector3
from engine.tools.move.move_command import move_entity


class CopyPreview:
    """Non-committing copy preview using cloned transient entities."""

    def __init__(self, entities: list[Any]) -> None:
        """Create copy preview state for selected source entities."""

        self.entities = list(entities)
        self.preview_entities: list[Any] = []
        self.delta = Vector3()
        self.copies = 1
        self.spacing = 0.0
        self.active = False

    def update(self, delta: Vector3, *, copies: int = 1, spacing: float = 0.0) -> None:
        """Rebuild preview entities for the current copy offset."""

        self.clear()
        self.delta = vector3(delta)
        self.copies = max(1, int(copies))
        self.spacing = float(spacing)
        if not delta_changed(self.delta):
            return
        self.preview_entities = self._build_preview()
        self.active = bool(self.preview_entities)

    def clear(self) -> None:
        """Clear transient preview entities."""

        self.preview_entities = []
        self.delta = Vector3()
        self.active = False

    def draw(self, painter: Any) -> None:
        """Draw copy preview entities using existing entity draw APIs."""

        for entity in self.preview_entities:
            draw = getattr(entity, "draw", None)
            if not callable(draw):
                continue
            previous = getattr(entity, "selected", False)
            entity.selected = True
            draw(painter)
            entity.selected = previous

    def _build_preview(self) -> list[Any]:
        """Build cloned preview entities without touching Workspace."""

        preview: list[Any] = []
        for copy_index in range(1, self.copies + 1):
            offset = self._offset_for_index(copy_index)
            for entity in self.entities:
                duplicate = clone_entity(entity)
                if duplicate is None:
                    continue
                move_entity(duplicate, offset)
                preview.append(duplicate)
        return preview

    def _offset_for_index(self, copy_index: int) -> Vector3:
        """Return preview offset for one copy index."""

        if self.spacing == 0.0:
            return self.delta * copy_index
        direction = self.delta.normalized()
        if direction.length_squared() == 0.0:
            direction = Vector3(1.0, 0.0, 0.0)
        return direction * (self.spacing * copy_index)
