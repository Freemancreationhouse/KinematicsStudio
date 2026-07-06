from abc import ABC, abstractmethod

from engine.geometry import BoundingBox


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
