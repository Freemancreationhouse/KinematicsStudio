from engine.geometry.vector3 import Vector3


class BoundingBox3D:
    """Axis-aligned 3D bounding box."""

    def __init__(self):

        self.min = Vector3(float("inf"), float("inf"), float("inf"))
        self.max = Vector3(float("-inf"), float("-inf"), float("-inf"))

    # --------------------------------

    @property
    def valid(self):
        """Return True when at least one point has been added."""

        return self.min.x <= self.max.x and self.min.y <= self.max.y and self.min.z <= self.max.z

    # --------------------------------

    @property
    def center(self):
        """Return the box center."""

        if not self.valid:
            return Vector3()

        return Vector3(
            (self.min.x + self.max.x) * 0.5,
            (self.min.y + self.max.y) * 0.5,
            (self.min.z + self.max.z) * 0.5,
        )

    # --------------------------------

    @property
    def size(self):
        """Return the box dimensions."""

        if not self.valid:
            return Vector3()

        return self.max - self.min

    # --------------------------------

    def add(self, point):
        """Expand the box to include a point."""

        self.min.x = min(self.min.x, point.x)
        self.min.y = min(self.min.y, point.y)
        self.min.z = min(self.min.z, point.z)
        self.max.x = max(self.max.x, point.x)
        self.max.y = max(self.max.y, point.y)
        self.max.z = max(self.max.z, point.z)

    # --------------------------------

    def corners(self):
        """Return the eight box corners."""

        if not self.valid:
            return []

        return [
            Vector3(x, y, z)
            for x in (self.min.x, self.max.x)
            for y in (self.min.y, self.max.y)
            for z in (self.min.z, self.max.z)
        ]
