from engine.geometry.vector3 import Vector3


class Plane:
    """3D plane represented by a normal and signed distance from origin."""

    def __init__(self, normal=None, distance=0.0):

        self.normal = (normal or Vector3(0.0, 0.0, 1.0)).normalized()
        self.distance = float(distance)

    # --------------------------------

    @staticmethod
    def from_point_normal(point, normal):
        """Create a plane from a point and normal."""

        unit = normal.normalized()
        return Plane(unit, -unit.dot(point))

    # --------------------------------

    def signed_distance(self, point):
        """Return signed distance from point to plane."""

        return self.normal.dot(point) + self.distance
