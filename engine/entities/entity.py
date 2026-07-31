from abc import ABC, abstractmethod

from engine.geometry import BoundingBox, BoundingBox3D, BoundingSphere, Vector3


class Entity(ABC):

    def __init__(self):

        self.selected = False
        self.visible = True
        self.locked = False
        self.layer = None
        self.layer_id = None
        self.layer_name = None
        self.color = None

    # --------------------------------

    @abstractmethod
    def draw(self, painter):
        pass

    # --------------------------------

    @abstractmethod
    def move(self, dx, dy):
        pass

    # --------------------------------

    @abstractmethod
    def clone(self):
        pass

    # --------------------------------

    @abstractmethod
    def hit_test(self, point):
        pass

    # --------------------------------

    @property
    @abstractmethod
    def bounding_box(self):
        pass

    # --------------------------------

    @property
    def type_name(self):

        return self.__class__.__name__

    # --------------------------------

    @property
    def display_color(self):
        """Return the effective display color for this entity."""

        layer = getattr(self, "layer", None)

        if layer is not None and getattr(layer, "color", None):
            return layer.color

        if self.color:
            return self.color

        return "#e0e0e0"

    # --------------------------------

    @property
    def bounding_box3d(self):
        """Return this 2D entity's shared-scene bounds on the XY plane."""

        box = BoundingBox3D()
        bounds = self.bounding_box
        box.add(Vector3(bounds.min.x, bounds.min.y, 0.0))
        box.add(Vector3(bounds.max.x, bounds.max.y, 0.0))
        return box

    # --------------------------------

    @property
    def bounding_sphere(self):
        """Return a 3D picking sphere for the projected XY bounds."""

        return BoundingSphere.from_box(self.bounding_box3d)
