from engine.blocks.block_definition import BlockDefinition


class BlockManager:
    """Owns block definitions and enforces stable IDs and unique names."""

    def __init__(self):

        self.definitions = []
        self._by_name = {}
        self._by_id = {}
        self._next_id = 0

    # --------------------------------

    def create_definition(self, name, origin=None, entities=None):
        """Create or return a uniquely named block definition."""

        clean_name = str(name).strip()

        if clean_name in self._by_name:
            return self._by_name[clean_name]

        definition = BlockDefinition(
            clean_name,
            block_id=self._next_id,
            origin=origin,
            entities=entities,
        )
        self._next_id += 1
        self.definitions.append(definition)
        self._by_name[definition.name] = definition
        self._by_id[definition.id] = definition

        return definition

    # --------------------------------

    def create(self, name, origin=None, entities=None):
        """Backward-compatible shorthand for definition creation."""

        return self.create_definition(name, origin, entities)

    # --------------------------------

    def get(self, value):
        """Return a block definition by name or ID."""

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

    # --------------------------------

    def get_by_id(self, block_id):
        """Return a block definition by stable numeric ID."""

        return self._by_id.get(block_id)

    # --------------------------------

    def names(self):
        """Return block definition names in creation order."""

        return [definition.name for definition in self.definitions]

    # --------------------------------

    @property
    def count(self):

        return len(self.definitions)
