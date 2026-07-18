from uuid import uuid4


class SceneCollection:
    """Reusable 3D scene collection for organizing existing entities."""

    def __init__(
        self,
        name="Collection",
        collection_id=None,
        parent_id=None,
        visible=True,
        locked=False,
        isolated=False,
        color_tag="#78909c",
    ):

        self.id = collection_id or str(uuid4())
        self.name = str(name)
        self.parent_id = parent_id
        self.visible = bool(visible)
        self.locked = bool(locked)
        self.isolated = bool(isolated)
        self.color_tag = color_tag
        self.entity_names = []

    # --------------------------------

    def add_entity(self, entity):
        """Reference an existing entity by stable name."""

        name = _entity_name(entity)

        if name not in self.entity_names:
            self.entity_names.append(name)

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity reference from this collection."""

        name = _entity_name(entity)

        if name in self.entity_names:
            self.entity_names.remove(name)

    # --------------------------------

    def contains(self, entity):
        """Return True when the collection references an entity."""

        return _entity_name(entity) in self.entity_names

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe collection data."""

        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "visible": self.visible,
            "locked": self.locked,
            "isolated": self.isolated,
            "color_tag": self.color_tag,
            "entity_names": list(self.entity_names),
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a collection from persisted data."""

        data = data or {}
        collection = SceneCollection(
            data.get("name", "Collection"),
            data.get("id"),
            data.get("parent_id"),
            data.get("visible", True),
            data.get("locked", False),
            data.get("isolated", False),
            data.get("color_tag", "#78909c"),
        )
        collection.entity_names = list(data.get("entity_names", []))

        return collection


class SceneCollectionManager:
    """Workspace-owned 3D scene collection manager."""

    def __init__(self):

        self.collections = []
        self.active = None

    # --------------------------------

    def create(self, name="Collection", parent=None, color_tag="#78909c"):
        """Create a unique scene collection."""

        collection = SceneCollection(
            self._unique_name(name),
            parent_id=self._collection_id(parent),
            color_tag=color_tag,
        )

        return self.add(collection)

    # --------------------------------

    def add(self, collection):
        """Store a scene collection."""

        if collection not in self.collections:
            collection.name = self._unique_name(collection.name, collection)
            self.collections.append(collection)

        if self.active is None:
            self.active = collection

        return collection

    # --------------------------------

    def rename(self, collection, new_name):
        """Rename a scene collection."""

        target = self.get(collection)

        if target is None:
            return False

        target.name = self._unique_name(new_name, target)

        return True

    # --------------------------------

    def delete(self, collection):
        """Delete a scene collection and reparent children to its parent."""

        target = self.get(collection)

        if target is None:
            return False

        for child in self.children(target):
            child.parent_id = target.parent_id

        self.collections.remove(target)

        if self.active is target:
            self.active = self.collections[0] if self.collections else None

        return True

    # --------------------------------

    def move_entity(self, entity, collection):
        """Move an entity reference to the target collection."""

        target = self.get(collection)

        if target is None:
            return False

        for item in self.collections:
            item.remove_entity(entity)

        target.add_entity(entity)

        return True

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity from every collection."""

        for item in self.collections:
            item.remove_entity(entity)

    # --------------------------------

    def entity_collection(self, entity):
        """Return the collection containing an entity."""

        for item in self.collections:
            if item.contains(entity):
                return item

        return None

    # --------------------------------

    def entity_visible(self, entity):
        """Return True when collection visibility allows an entity."""

        isolated = self.isolated_collections()

        if isolated and not any(collection.contains(entity) for collection in isolated):
            return False

        collection = self.entity_collection(entity)

        if collection is None:
            return not isolated

        return self._collection_branch_visible(collection)

    # --------------------------------

    def entity_locked(self, entity):
        """Return True when collection lock state protects an entity."""

        collection = self.entity_collection(entity)

        if collection is None:
            return False

        while collection is not None:
            if collection.locked:
                return True

            collection = self.get(collection.parent_id)

        return False

    # --------------------------------

    def isolated_collections(self):
        """Return isolated collections."""

        return [
            collection for collection in self.collections
            if collection.isolated
        ]

    # --------------------------------

    def children(self, collection):
        """Return nested child collections."""

        target_id = self._collection_id(collection)

        return [
            item for item in self.collections
            if item.parent_id == target_id
        ]

    # --------------------------------

    def get(self, collection):
        """Return collection by object, id or name."""

        if isinstance(collection, SceneCollection):
            return collection if collection in self.collections else None

        for item in self.collections:
            if item.id == collection or item.name == collection:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return collection names."""

        return [collection.name for collection in self.collections]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe collection manager data."""

        return {
            "active": getattr(self.active, "id", None),
            "collections": [collection.to_dict() for collection in self.collections],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore collection manager data."""

        data = data or {}
        self.collections = [
            SceneCollection.from_dict(item)
            for item in data.get("collections", [])
        ]
        self.active = self.get(data.get("active")) or (self.collections[0] if self.collections else None)

    # --------------------------------

    def _collection_branch_visible(self, collection):

        target = collection

        while target is not None:
            if not target.visible:
                return False

            target = self.get(target.parent_id)

        return True

    # --------------------------------

    def _collection_id(self, collection):

        target = self.get(collection)

        return target.id if target is not None else None

    # --------------------------------

    def _unique_name(self, name, current=None):

        base = str(name or "Collection").strip() or "Collection"
        names = {
            collection.name for collection in self.collections
            if collection is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


class ViewFilter:
    """Reusable 3D view filter definition."""

    def __init__(
        self,
        name="View Filter",
        enabled=True,
        layer_names=None,
        entity_types=None,
        collection_names=None,
        visibility=None,
        selected=None,
        locked=None,
        include_measurements=True,
        include_sections=True,
        custom=None,
    ):

        self.name = str(name)
        self.enabled = bool(enabled)
        self.layer_names = list(layer_names or [])
        self.entity_types = list(entity_types or [])
        self.collection_names = list(collection_names or [])
        self.visibility = visibility
        self.selected = selected
        self.locked = locked
        self.include_measurements = bool(include_measurements)
        self.include_sections = bool(include_sections)
        self.custom = custom

    # --------------------------------

    def matches(self, entity, workspace):
        """Return True when an entity satisfies this filter."""

        if not self.enabled:
            return True

        if getattr(entity, "is_measurement", False) and not self.include_measurements:
            return False

        if getattr(entity, "is_section", False) and not self.include_sections:
            return False

        if self.layer_names and getattr(entity, "layer_name", None) not in self.layer_names:
            return False

        if self.entity_types and getattr(entity, "type_name", entity.__class__.__name__) not in self.entity_types:
            return False

        if self.collection_names:
            manager = getattr(workspace, "scene_collection_manager", None)
            collection = manager.entity_collection(entity) if manager is not None else None

            if collection is None or collection.name not in self.collection_names:
                return False

        if self.visibility is not None and bool(getattr(entity, "visible", True)) != bool(self.visibility):
            return False

        if self.selected is not None and bool(getattr(entity, "selected", False)) != bool(self.selected):
            return False

        if self.locked is not None and bool(getattr(entity, "locked", False)) != bool(self.locked):
            return False

        if self.custom is not None and not self.custom(entity, workspace):
            return False

        return True

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe filter data."""

        return {
            "name": self.name,
            "enabled": self.enabled,
            "layer_names": list(self.layer_names),
            "entity_types": list(self.entity_types),
            "collection_names": list(self.collection_names),
            "visibility": self.visibility,
            "selected": self.selected,
            "locked": self.locked,
            "include_measurements": self.include_measurements,
            "include_sections": self.include_sections,
            "custom": "runtime-only" if self.custom is not None else None,
        }

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a filter from persisted data."""

        data = data or {}

        return ViewFilter(
            data.get("name", "View Filter"),
            data.get("enabled", True),
            data.get("layer_names", []),
            data.get("entity_types", []),
            data.get("collection_names", []),
            data.get("visibility"),
            data.get("selected"),
            data.get("locked"),
            data.get("include_measurements", True),
            data.get("include_sections", True),
        )


class ViewFilterManager:
    """Workspace-owned view filter manager."""

    def __init__(self):

        self.filters = []
        self.active = None

    # --------------------------------

    def add(self, view_filter):
        """Store a view filter."""

        if view_filter not in self.filters:
            view_filter.name = self._unique_name(view_filter.name, view_filter)
            self.filters.append(view_filter)

        if self.active is None:
            self.active = view_filter

        return view_filter

    # --------------------------------

    def create(self, name="View Filter", **criteria):
        """Create a view filter."""

        return self.add(ViewFilter(self._unique_name(name), **criteria))

    # --------------------------------

    def delete(self, view_filter):
        """Delete a view filter."""

        target = self.get(view_filter)

        if target is None:
            return False

        self.filters.remove(target)

        if self.active is target:
            self.active = self.filters[0] if self.filters else None

        return True

    # --------------------------------

    def set_active(self, view_filter):
        """Set active view filter."""

        if view_filter is None:
            self.active = None
            return None

        target = self.get(view_filter)

        if target is not None:
            self.active = target

        return self.active

    # --------------------------------

    def matches(self, entity, workspace):
        """Return True when active filters allow an entity."""

        if not self.filters:
            return True

        active_filters = [
            view_filter for view_filter in self.filters
            if view_filter.enabled
        ]

        if not active_filters:
            return True

        return all(view_filter.matches(entity, workspace) for view_filter in active_filters)

    # --------------------------------

    def get(self, view_filter):
        """Return filter by object or name."""

        if isinstance(view_filter, ViewFilter):
            return view_filter if view_filter in self.filters else None

        for item in self.filters:
            if item.name == view_filter:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return filter names."""

        return [view_filter.name for view_filter in self.filters]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe filter manager data."""

        return {
            "active": getattr(self.active, "name", None),
            "filters": [view_filter.to_dict() for view_filter in self.filters],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore filter manager data."""

        data = data or {}
        self.filters = [
            ViewFilter.from_dict(item)
            for item in data.get("filters", [])
        ]
        self.active = self.get(data.get("active")) or (self.filters[0] if self.filters else None)

    # --------------------------------

    def _unique_name(self, name, current=None):

        base = str(name or "View Filter").strip() or "View Filter"
        names = {
            view_filter.name for view_filter in self.filters
            if view_filter is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


class DisplayPreset:
    """Reusable display preset for view filters, display mode and visual style."""

    def __init__(
        self,
        name="Display Preset",
        display_mode="wireframe",
        visual_style="Default",
        view_filter=None,
        isolated_collections=None,
    ):

        self.name = str(name)
        self.display_mode = display_mode
        self.visual_style = visual_style
        self.view_filter = view_filter
        self.isolated_collections = list(isolated_collections or [])

    # --------------------------------

    @staticmethod
    def capture(name, workspace):
        """Capture a display preset from current workspace display state."""

        active_filter = getattr(workspace.view_filter_manager, "active", None)
        isolated = [
            collection.name
            for collection in workspace.scene_collection_manager.isolated_collections()
        ]

        return DisplayPreset(
            name,
            workspace.display_mode_manager.current_mode,
            getattr(workspace.visual_style_manager.current, "name", "Default"),
            getattr(active_filter, "name", None),
            isolated,
        )

    # --------------------------------

    def restore(self, workspace):
        """Apply this preset to workspace managers."""

        workspace.display_mode_manager.set_mode(self.display_mode)
        workspace.visual_style_manager.set_current(self.visual_style)
        workspace.view_filter_manager.set_active(self.view_filter)

        isolated = set(self.isolated_collections)

        for collection in workspace.scene_collection_manager.collections:
            collection.isolated = collection.name in isolated

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe display preset data."""

        return dict(self.__dict__)

    # --------------------------------

    @staticmethod
    def from_dict(data):
        """Create a display preset from persisted data."""

        data = data or {}

        return DisplayPreset(
            data.get("name", "Display Preset"),
            data.get("display_mode", "wireframe"),
            data.get("visual_style", "Default"),
            data.get("view_filter"),
            data.get("isolated_collections", []),
        )


class DisplayPresetManager:
    """Workspace-owned display preset manager."""

    def __init__(self):

        self.presets = []
        self.active = None

    # --------------------------------

    def save(self, name, workspace):
        """Save a display preset from current workspace state."""

        preset = DisplayPreset.capture(self._unique_name(name), workspace)

        return self.add(preset)

    # --------------------------------

    def add(self, preset):
        """Store a display preset."""

        if preset not in self.presets:
            preset.name = self._unique_name(preset.name, preset)
            self.presets.append(preset)

        if self.active is None:
            self.active = preset

        return preset

    # --------------------------------

    def restore(self, preset, workspace):
        """Restore a display preset."""

        target = self.get(preset)

        if target is None:
            return None

        target.restore(workspace)
        self.active = target

        return target

    # --------------------------------

    def rename(self, preset, new_name):
        """Rename a display preset."""

        target = self.get(preset)

        if target is None:
            return False

        target.name = self._unique_name(new_name, target)

        return True

    # --------------------------------

    def delete(self, preset):
        """Delete a display preset."""

        target = self.get(preset)

        if target is None:
            return False

        self.presets.remove(target)

        if self.active is target:
            self.active = self.presets[0] if self.presets else None

        return True

    # --------------------------------

    def get(self, preset):
        """Return preset by object or name."""

        if isinstance(preset, DisplayPreset):
            return preset if preset in self.presets else None

        for item in self.presets:
            if item.name == preset:
                return item

        return None

    # --------------------------------

    def names(self):
        """Return preset names."""

        return [preset.name for preset in self.presets]

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe preset manager data."""

        return {
            "active": getattr(self.active, "name", None),
            "presets": [preset.to_dict() for preset in self.presets],
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore display presets."""

        data = data or {}
        self.presets = [
            DisplayPreset.from_dict(item)
            for item in data.get("presets", [])
        ]
        self.active = self.get(data.get("active")) or (self.presets[0] if self.presets else None)

    # --------------------------------

    def _unique_name(self, name, current=None):

        base = str(name or "Display Preset").strip() or "Display Preset"
        names = {
            preset.name for preset in self.presets
            if preset is not current
        }

        if base not in names:
            return base

        index = 1

        while f"{base} {index}" in names:
            index += 1

        return f"{base} {index}"


def _entity_name(entity):

    return str(getattr(entity, "name", id(entity)))
