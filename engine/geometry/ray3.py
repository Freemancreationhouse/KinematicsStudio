from engine.geometry.vector3 import Vector3


class Ray3:
    """3D ray with origin and normalized direction."""

    def __init__(self, origin=None, direction=None):

        self.origin = origin or Vector3()
        self.direction = (direction or Vector3(0.0, 0.0, -1.0)).normalized()

    # --------------------------------

    def point_at(self, distance):
        """Return a point along the ray."""

        return self.origin + self.direction * distance
