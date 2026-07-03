from engine.geometry.vector2 import Vector2


class BoundingBox:

    def __init__(self):

        self.reset()

    # --------------------------------

    def reset(self):

        self.min = Vector2(float("inf"), float("inf"))
        self.max = Vector2(float("-inf"), float("-inf"))

    # --------------------------------

    def add(self, point):

        self.min.x = min(self.min.x, point.x)
        self.min.y = min(self.min.y, point.y)

        self.max.x = max(self.max.x, point.x)
        self.max.y = max(self.max.y, point.y)

    # --------------------------------

    @property
    def width(self):

        return self.max.x - self.min.x

    @property
    def height(self):

        return self.max.y - self.min.y

    @property
    def center(self):

        return Vector2(

            (self.min.x + self.max.x) * 0.5,

            (self.min.y + self.max.y) * 0.5

        )

    # --------------------------------

    def __repr__(self):

        return f"BoundingBox({self.min}, {self.max})"