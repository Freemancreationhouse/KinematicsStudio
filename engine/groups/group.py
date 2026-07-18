class Group:
    """Named collection of references to existing workspace entities."""

    def __init__(self, name, group_id=None, entities=None):

        self.id = group_id
        self.name = str(name).strip()
        self.entities = []

        for entity in entities or []:
            self.add(entity)

    # --------------------------------

    def add(self, entity):
        """Add an existing entity reference to this group."""

        if entity not in self.entities:
            self.entities.append(entity)

        return entity

    # --------------------------------

    def remove(self, entity):
        """Remove an entity reference from this group."""

        if entity in self.entities:
            self.entities.remove(entity)

        return entity

    # --------------------------------

    def contains(self, entity):
        """Return True when entity belongs to this group."""

        return entity in self.entities

    # --------------------------------

    @property
    def count(self):

        return len(self.entities)
