from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox


class PolylineEntity(Entity):

    def __init__(self, points=None):

        super().__init__()

        self.points = points[:] if points else []

    # --------------------------------

    def draw(self, painter):

        pass

    # --------------------------------

    def add_point(self, point):

        self.points.append(point)

    # --------------------------------

    def move(self, dx, dy):

        for p in self.points:

            p.x += dx
            p.y += dy

    # --------------------------------

    def clone(self):

        return PolylineEntity(

            [p.copy() for p in self.points]

        )

    # --------------------------------

    def hit_test(self, point):

        return False

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        for p in self.points:

            box.add(p)

        return box

    # --------------------------------

    @property
    def count(self):

        return len(self.points)