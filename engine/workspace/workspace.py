from engine.commands import CommandManager
from engine.workspace.selection_manager import SelectionManager


class Workspace:
    """Owns model entities, selection state, and command history."""

    def __init__(self, name="Workspace"):

        self.name = name

        self.entities = []

        self.selection = SelectionManager()

        self.command_manager = CommandManager()

    # --------------------------------

    def add_entity(self, entity):
        """Store an entity in this workspace."""

        self.entities.append(entity)

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity from this workspace if present."""

        if entity in self.entities:

            self.entities.remove(entity)

    # --------------------------------

    def clear(self):
        """Remove all entities from this workspace."""

        self.entities.clear()

    # --------------------------------

    def visible_entities(self):
        """Return entities currently available for rendering and snapping."""

        return [
            entity for entity in self.entities
            if getattr(entity, "visible", True)
        ]

    # --------------------------------

    def selectable_entities(self):
        """Return visible entities that are not locked."""

        return [
            entity for entity in self.visible_entities()
            if not getattr(entity, "locked", False)
        ]

    # --------------------------------

    def bounds(self):
        """Return the combined bounding box of visible entities."""

        visible = self.visible_entities()

        if not visible:
            return None

        from engine.geometry import BoundingBox

        bounds = BoundingBox()

        for entity in visible:
            box = entity.bounding_box
            bounds.add(box.min)
            bounds.add(box.max)

        return bounds

    # --------------------------------

    def snap_candidates(self):
        """Return visible entities that can participate in snapping."""

        return self.visible_entities()

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)
