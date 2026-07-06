# DEPRECATED: Legacy line entity retained for backward compatibility.
# V2 uses engine.entities.line_entity.LineEntity.

from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox


class LineEntity(Entity):

    def __init__(self, start=None, end=None):

        super().__init__()

        self.start = start or Vector2()
        self.end = end or Vector2()

    # --------------------------------

    def draw(self, painter):

        pass

    # --------------------------------

    def move(self, dx, dy):

        self.start.x += dx
        self.start.y += dy

        self.end.x += dx
        self.end.y += dy

    # --------------------------------

    def clone(self):

        return LineEntity(

            self.start.copy(),

            self.end.copy()

        )

    # --------------------------------

    def hit_test(self, point):

        return False

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        box.add(self.start)

        box.add(self.end)

        return box
