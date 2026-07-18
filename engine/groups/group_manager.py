from engine.groups.group import Group


class GroupManager:
    """Owns professional groups for a workspace."""

    def __init__(self):

        self.groups = []
        self._by_name = {}
        self._by_id = {}
        self._next_id = 0
        self.current = None
        self.selection_enabled = True

    # --------------------------------

    def create(self, name, entities=None):
        """Create a unique group containing existing entity references."""

        clean_name = self.unique_name(name)
        group = Group(clean_name, self._next_id, entities)
        self._next_id += 1
        self.groups.append(group)
        self._by_name[group.name] = group
        self._by_id[group.id] = group
        self.current = group

        return group

    # --------------------------------

    def remove(self, group):
        """Remove a group without deleting its member entities."""

        target = self._coerce_group(group)

        if target is None:
            return False

        self.groups.remove(target)
        self._by_name.pop(target.name, None)
        self._by_id.pop(target.id, None)

        if self.current is target:
            self.current = self.groups[0] if self.groups else None

        return True

    # --------------------------------

    def rename(self, group, new_name):
        """Rename a group while preserving its ID."""

        target = self._coerce_group(group)
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

    def add_entity(self, group, entity):
        """Add an entity reference to a group."""

        target = self._coerce_group(group)

        if target is None:
            return False

        target.add(entity)

        return True

    # --------------------------------

    def remove_entity(self, group, entity):
        """Remove an entity reference from a group."""

        target = self._coerce_group(group)

        if target is None:
            return False

        target.remove(entity)

        return True

    # --------------------------------

    def groups_for_entity(self, entity):
        """Return every group containing an entity."""

        return [
            group for group in self.groups
            if group.contains(entity)
        ]

    # --------------------------------

    def primary_group_for_entity(self, entity):
        """Return the first group containing an entity."""

        groups = self.groups_for_entity(entity)

        return groups[0] if groups else None

    # --------------------------------

    def expand_selection(self, entity):
        """Return group members when group selection is enabled."""

        if not self.selection_enabled:
            return [entity]

        group = self.primary_group_for_entity(entity)

        return list(group.entities) if group is not None else [entity]

    # --------------------------------

    def unregister_entity(self, entity):
        """Remove an entity reference from every group."""

        for group in list(self.groups):
            group.remove(entity)

    # --------------------------------

    def get(self, value):
        """Return a group by name or ID."""

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

    # --------------------------------

    def get_by_id(self, group_id):
        """Return a group by numeric ID."""

        return self._by_id.get(group_id)

    # --------------------------------

    def set_current(self, group):
        """Set the current group by object, name, or ID."""

        target = self._coerce_group(group)

        if target is not None:
            self.current = target

        return self.current

    # --------------------------------

    def unique_name(self, name):
        """Return a group name that does not collide with existing names."""

        base = str(name).strip() or "Group"

        if base not in self._by_name:
            return base

        index = 1

        while f"{base} {index}" in self._by_name:
            index += 1

        return f"{base} {index}"

    # --------------------------------

    def names(self):
        """Return group names in creation order."""

        return [group.name for group in self.groups]

    # --------------------------------

    def _coerce_group(self, value):

        if isinstance(value, Group):
            return self._by_id.get(value.id)

        if isinstance(value, int):
            return self._by_id.get(value)

        return self._by_name.get(value)

    # --------------------------------

    @property
    def count(self):

        return len(self.groups)
