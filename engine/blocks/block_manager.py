from engine.blocks.block_definition import BlockDefinition


class BlockManager:
    """Owns block definitions and enforces stable IDs and unique names."""

    def __init__(self):

        self.definitions = []
        self._by_name = {}
        self._by_id = {}
        self._next_id = 0
        self.current = None

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

        if self.would_create_cycle(definition, definition.entities):
            raise ValueError("Block definition cannot reference itself")

        self._next_id += 1
        self.definitions.append(definition)
        self._by_name[definition.name] = definition
        self._by_id[definition.id] = definition
        self.current = definition

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

    def rename(self, definition, new_name):
        """Rename a block definition while preserving its stable ID."""

        target = self._coerce_definition(definition)
        clean_name = str(new_name).strip()

        if target is None or not clean_name:
            return False

        if clean_name in self._by_name and self._by_name[clean_name] is not target:
            return False

        self._by_name.pop(target.name, None)
        target.name = clean_name
        self._by_name[target.name] = target

        return True

    # --------------------------------

    def remove(self, definition):
        """Remove a block definition when no references depend on it."""

        target = self._coerce_definition(definition)

        if target is None:
            return False

        self.definitions.remove(target)
        self._by_name.pop(target.name, None)
        self._by_id.pop(target.id, None)

        if self.current is target:
            self.current = self.definitions[0] if self.definitions else None

        return True

    # --------------------------------

    def can_update(self, definition, entities):
        """Return True when entities can be stored without circular nesting."""

        target = self._coerce_definition(definition)

        if target is None:
            return False

        return not self.would_create_cycle(target, entities)

    # --------------------------------

    def would_create_cycle(self, definition, entities):
        """Return True if entities would recursively contain definition."""

        for entity in entities or []:
            child = getattr(entity, "definition", None)

            if child is None:
                continue

            if child is definition:
                return True

            if self._definition_reaches(child, definition, set()):
                return True

        return False

    # --------------------------------

    def has_circular_references(self):
        """Return True if any stored definition participates in a cycle."""

        return any(
            self.would_create_cycle(definition, definition.entities)
            for definition in self.definitions
        )

    # --------------------------------

    def _definition_reaches(self, source, target, visited):

        if source is target:
            return True

        if source in visited:
            return False

        visited.add(source)

        for entity in getattr(source, "entities", []):
            child = getattr(entity, "definition", None)

            if child is not None and self._definition_reaches(child, target, visited):
                return True

        return False

    # --------------------------------

    def set_current(self, definition):
        """Set the current definition by object, name, or ID."""

        target = self._coerce_definition(definition)

        if target is not None:
            self.current = target

        return self.current

    # --------------------------------

    def unique_name(self, name):
        """Return a block name that does not collide with existing names."""

        base = str(name).strip() or "Block"

        if base not in self._by_name:
            return base

        index = 1

        while f"{base} {index}" in self._by_name:
            index += 1

        return f"{base} {index}"

    # --------------------------------

    def names(self):
        """Return block definition names in creation order."""

        return [definition.name for definition in self.definitions]

    # --------------------------------

    def _coerce_definition(self, value):

        if isinstance(value, BlockDefinition):
            return self._by_id.get(value.id)

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

    # --------------------------------

    @property
    def count(self):

        return len(self.definitions)
