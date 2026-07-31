from engine.geometry import BoundingBox3D, Matrix4


class SceneNode:
    """Node in the workspace-owned 3D scene hierarchy."""

    def __init__(self, name="SceneNode", entity=None, transform=None):

        self.name = name
        self.entity = entity
        self.transform = transform or Matrix4.identity()
        self.parent = None
        self.children = []
        self.visible = True
        self.bounding_box = BoundingBox3D()
        self.update_bounds()

    # --------------------------------

    def add_child(self, node):
        """Attach a child node."""

        node.parent = self
        self.children.append(node)
        self.update_bounds()

        return node

    # --------------------------------

    def remove_child(self, node):
        """Remove a child node."""

        if node in self.children:
            self.children.remove(node)
            node.parent = None
            self.update_bounds()

    # --------------------------------

    def world_transform(self):
        """Return this node's world transform."""

        if self.parent is None:
            return self.transform

        return self.parent.world_transform() @ self.transform

    # --------------------------------

    def effective_visible(self):
        """Return visibility after parent propagation."""

        if not self.visible:
            return False

        if self.entity is not None and not getattr(self.entity, "visible", True):
            return False

        if self.parent is None:
            return True

        return self.parent.effective_visible()

    # --------------------------------

    def update_bounds(self):
        """Refresh bounding data from entity and children."""

        self.bounding_box = BoundingBox3D()

        if self.entity is not None:
            for point in self.entity.bounding_box3d.corners():
                self.bounding_box.add(point)

        for child in self.children:
            child.update_bounds()

            for point in child.bounding_box.corners():
                self.bounding_box.add(point)

        return self.bounding_box

    # --------------------------------

    def walk(self):
        """Yield this node and all descendants."""

        yield self

        for child in self.children:
            yield from child.walk()


class Scene3D:
    """Workspace-owned scene graph facade for shared model entities."""

    def __init__(self, entity_source=None):

        self.root = SceneNode("Scene3D")
        self.nodes = []
        self.entity_source = entity_source

    # --------------------------------

    def set_entity_source(self, entity_source):
        """Use a workspace-owned entity list as the scene's entity source."""

        self.entity_source = entity_source

    # --------------------------------

    def add_entity(self, entity, parent=None):
        """Add an entity to the shared scene without duplicating storage."""

        if self.entity_source is not None and parent is None:
            if entity not in self.entity_source:
                self.entity_source.append(entity)
            return entity

        node = SceneNode(getattr(entity, "name", entity.type_name), entity)
        target = parent or self.root
        target.add_child(node)
        self.nodes.append(node)

        return node

    # --------------------------------

    def remove_entity(self, entity):
        """Remove an entity from the shared scene."""

        if self.entity_source is not None:
            if entity in self.entity_source:
                self.entity_source.remove(entity)
                return True
            return False

        for node in list(self.nodes):
            if node.entity is entity:
                if node.parent:
                    node.parent.remove_child(node)
                self.nodes.remove(node)
                return True

        return False

    # --------------------------------

    def entities(self):
        """Return scene entities in traversal order."""

        if self.entity_source is not None:
            return list(self.entity_source)

        return [
            node.entity
            for node in self.nodes
            if node.entity is not None
        ]

    # --------------------------------

    def visible_entities(self):
        """Return visible scene entities."""

        if self.entity_source is not None:
            return [
                entity for entity in self.entity_source
                if getattr(entity, "visible", True)
            ]

        return [
            node.entity
            for node in self.nodes
            if node.entity is not None and node.effective_visible()
        ]

    # --------------------------------

    def clear(self):
        """Clear all scene nodes."""

        if self.entity_source is not None:
            self.entity_source.clear()
        self.root.children.clear()
        self.nodes.clear()

    # --------------------------------

    def bounds(self):
        """Return aggregate scene bounds."""

        self.root.update_bounds()

        return self.root.bounding_box

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe scene data."""

        return {
            "entities": [
                entity.to_dict()
                for entity in self.entities()
                if (
                    getattr(entity, "is_3d", False) and
                    hasattr(entity, "to_dict")
                )
            ],
        }
