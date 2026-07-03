from math import sqrt


class Vector:

    def __init__(self, x=0.0, y=0.0, z=0.0):

        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # ----------------------------

    def __add__(self, other):

        return Vector(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    # ----------------------------

    def __sub__(self, other):

        return Vector(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        )

    # ----------------------------

    def __mul__(self, value):

        return Vector(
            self.x * value,
            self.y * value,
            self.z * value
        )

    # ----------------------------

    def length(self):

        return sqrt(
            self.x * self.x +
            self.y * self.y +
            self.z * self.z
        )

    # ----------------------------

    def normalize(self):

        l = self.length()

        if l == 0:
            return Vector()

        return Vector(
            self.x / l,
            self.y / l,
            self.z / l
        )

    # ----------------------------

    def dot(self, other):

        return (
            self.x * other.x +
            self.y * other.y +
            self.z * other.z
        )

    # ----------------------------

    def cross(self, other):

        return Vector(

            self.y * other.z - self.z * other.y,

            self.z * other.x - self.x * other.z,

            self.x * other.y - self.y * other.x

        )

    # ----------------------------

    def tuple(self):

        return (
            self.x,
            self.y,
            self.z
        )

    def __repr__(self):

        return f"Vector({self.x}, {self.y}, {self.z})"