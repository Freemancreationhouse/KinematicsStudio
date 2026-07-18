import math

from engine.geometry.vector3 import Vector3


class Quaternion:
    """Quaternion rotation primitive for future 3D tools and cameras."""

    def __init__(self, x=0.0, y=0.0, z=0.0, w=1.0):

        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    # --------------------------------

    @staticmethod
    def from_axis_angle(axis, angle_degrees):
        """Create a quaternion from an axis and angle in degrees."""

        normalized = axis.normalized()
        radians = math.radians(angle_degrees) * 0.5
        scale = math.sin(radians)

        return Quaternion(
            normalized.x * scale,
            normalized.y * scale,
            normalized.z * scale,
            math.cos(radians),
        ).normalized()

    # --------------------------------

    def normalized(self):
        """Return a unit quaternion."""

        length = math.sqrt(
            self.x * self.x +
            self.y * self.y +
            self.z * self.z +
            self.w * self.w
        )

        if length == 0.0:
            return Quaternion()

        return Quaternion(
            self.x / length,
            self.y / length,
            self.z / length,
            self.w / length,
        )

    # --------------------------------

    def rotate_vector(self, vector):
        """Rotate a vector by this quaternion."""

        q_vector = Vector3(self.x, self.y, self.z)
        uv = q_vector.cross(vector)
        uuv = q_vector.cross(uv)

        return vector + (uv * (2.0 * self.w)) + (uuv * 2.0)

    # --------------------------------

    def __mul__(self, other):

        return Quaternion(
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w,
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
        )
