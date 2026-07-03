from engine.geometry.vector2 import Vector2
from engine.geometry.bounding_box import BoundingBox


class Polygon2:

    def __init__(self):

        self.points = []

    # --------------------------------

    def add(self, point):

        self.points.append(point)

    # --------------------------------

    @property
    def count(self):

        return len(self.points)

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        for p in self.points:

            box.add(p)

        return box

    # --------------------------------

    @property
    def center(self):

        if not self.points:

            return Vector2()

        sx = sum(p.x for p in self.points)
        sy = sum(p.y for p in self.points)

        return Vector2(

            sx / len(self.points),

            sy / len(self.points)

        )

    # --------------------------------

    def translate(self, dx, dy):

        for p in self.points:

            p.x += dx
            p.y += dy

    # --------------------------------

    def __repr__(self):

        return f"Polygon2({len(self.points)} points)"