from engine.blocks.block import Block


class BlockDefinition(Block):
    """Reusable block definition containing source entities."""

    def __init__(self, name, block_id=None, origin=None, entities=None):

        super().__init__(name, block_id, origin)
        self.entities = []

        for entity in entities or []:
            self.add_entity(entity)

    # --------------------------------

    def add_entity(self, entity):
        """Add an entity to this block definition."""

        if entity not in self.entities:
            self.entities.append(entity)

        return entity

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity from this block definition."""

        if entity in self.entities:
            self.entities.remove(entity)

        return entity

    # --------------------------------

    def clone_entities(self):
        """Return cloned definition entities for future editing workflows."""

        return [self._clone_entity(entity) for entity in self.entities]

    # --------------------------------

    def _clone_entity(self, entity):

        clone = entity.clone()
        clone.selected = False
        clone.visible = getattr(entity, "visible", True)
        clone.locked = getattr(entity, "locked", False)
        clone.layer = getattr(entity, "layer", None)
        clone.layer_id = getattr(entity, "layer_id", None)
        clone.layer_name = getattr(entity, "layer_name", None)
        clone.color = getattr(entity, "color", None)

        return clone

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)
