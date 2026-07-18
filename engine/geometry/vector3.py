import math


class Vector3:
    """Three-dimensional vector used by the reusable 3D foundation."""

    def __init__(self, x=0.0, y=0.0, z=0.0):

        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # --------------------------------

    def copy(self):
        """Return a detached vector copy."""

        return Vector3(self.x, self.y, self.z)

    # --------------------------------

    def length(self):
        """Return the vector magnitude."""

        return math.sqrt(self.length_squared())

    # --------------------------------

    def length_squared(self):
        """Return the squared vector magnitude."""

        return self.x * self.x + self.y * self.y + self.z * self.z

    # --------------------------------

    def normalized(self):
        """Return a unit-length vector, or zero when degenerate."""

        magnitude = self.length()

        if magnitude <= 0.0:
            return Vector3()

        return self / magnitude

    # --------------------------------

    def dot(self, other):
        """Return the dot product with another vector."""

        return self.x * other.x + self.y * other.y + self.z * other.z

    # --------------------------------

    def cross(self, other):
        """Return the cross product with another vector."""

        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    # --------------------------------

    def distance_to(self, other):
        """Return distance to another vector."""

        return (self - other).length()

    # --------------------------------

    def to_tuple(self):
        """Return a plain tuple representation."""

        return (self.x, self.y, self.z)

    # --------------------------------

    def __add__(self, other):

        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    # --------------------------------

    def __sub__(self, other):

        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    # --------------------------------

    def __mul__(self, scalar):

        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    # --------------------------------

    def __truediv__(self, scalar):

        if scalar == 0:
            return Vector3()

        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    # --------------------------------

    def __neg__(self):

        return Vector3(-self.x, -self.y, -self.z)

    # --------------------------------

    def __repr__(self):

        return f"Vector3({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"
