from engine.geometry.vector2 import Vector2


class Ray2:

    def __init__(self, origin=None, direction=None):

        self.origin = origin or Vector2()
        self.direction = (direction or Vector2(1, 0)).normalized()

    # --------------------------------

    def point_at(self, distance):

        return self.origin + self.direction * distance

    # --------------------------------

    def __repr__(self):

        return f"Ray2(origin={self.origin}, direction={self.direction})"