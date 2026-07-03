from engine.geometry.vector2 import Vector2


class Segment2:

    def __init__(self, start=None, end=None):

        self.start = start or Vector2()
        self.end = end or Vector2()

    # --------------------------------

    @property
    def length(self):

        return self.start.distance_to(self.end)

    # --------------------------------

    @property
    def direction(self):

        return (self.end - self.start).normalized()

    # --------------------------------

    @property
    def midpoint(self):

        return Vector2(

            (self.start.x + self.end.x) * 0.5,

            (self.start.y + self.end.y) * 0.5

        )

    # --------------------------------

    def reverse(self):

        self.start, self.end = self.end, self.start

    # --------------------------------

    def __repr__(self):

        return f"Segment2({self.start}, {self.end})"