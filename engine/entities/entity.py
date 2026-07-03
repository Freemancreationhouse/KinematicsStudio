from abc import ABC, abstractmethod

from engine.geometry import BoundingBox


class Entity(ABC):

    def __init__(self):

        self.selected = False
        self.visible = True
        self.locked = False

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