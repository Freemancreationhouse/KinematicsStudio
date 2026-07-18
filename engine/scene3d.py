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
    """Workspace-owned 3D scene graph."""

    def __init__(self):

        self.root = SceneNode("Scene3D")
        self.nodes = []

    # --------------------------------

    def add_entity(self, entity, parent=None):
        """Add a 3D entity to the scene graph."""

        node = SceneNode(getattr(entity, "name", entity.type_name), entity)
        target = parent or self.root
        target.add_child(node)
        self.nodes.append(node)

        return node

    # --------------------------------

    def remove_entity(self, entity):
        """Remove a 3D entity from the scene graph."""

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

        return [
            node.entity
            for node in self.nodes
            if node.entity is not None
        ]

    # --------------------------------

    def visible_entities(self):
        """Return visible 3D scene entities."""

        return [
            node.entity
            for node in self.nodes
            if node.entity is not None and node.effective_visible()
        ]

    # --------------------------------

    def clear(self):
        """Clear all scene nodes."""

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
                node.entity.to_dict()
                for node in self.nodes
                if node.entity is not None
            ],
        }
