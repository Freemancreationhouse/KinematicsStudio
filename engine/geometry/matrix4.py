import math

from engine.geometry.vector3 import Vector3


class Matrix4:
    """Row-major 4x4 matrix for 3D transforms and projections."""

    def __init__(self, values=None):

        self.values = list(values) if values is not None else self.identity().values

    # --------------------------------

    @staticmethod
    def identity():
        """Return an identity matrix."""

        return Matrix4([
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ])

    # --------------------------------

    @staticmethod
    def translation(vector):
        """Return a translation matrix."""

        matrix = Matrix4.identity()
        matrix.values[3] = vector.x
        matrix.values[7] = vector.y
        matrix.values[11] = vector.z
        return matrix

    # --------------------------------

    @staticmethod
    def scaling(vector):
        """Return a non-uniform scaling matrix."""

        matrix = Matrix4.identity()
        matrix.values[0] = vector.x
        matrix.values[5] = vector.y
        matrix.values[10] = vector.z
        return matrix

    # --------------------------------

    @staticmethod
    def rotation_x(angle_degrees):
        """Return a rotation matrix around the X axis."""

        radians = math.radians(angle_degrees)
        c = math.cos(radians)
        s = math.sin(radians)

        return Matrix4([
            1.0, 0.0, 0.0, 0.0,
            0.0, c, -s, 0.0,
            0.0, s, c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ])

    # --------------------------------

    @staticmethod
    def rotation_y(angle_degrees):
        """Return a rotation matrix around the Y axis."""

        radians = math.radians(angle_degrees)
        c = math.cos(radians)
        s = math.sin(radians)

        return Matrix4([
            c, 0.0, s, 0.0,
            0.0, 1.0, 0.0, 0.0,
            -s, 0.0, c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ])

    # --------------------------------

    @staticmethod
    def rotation_z(angle_degrees):
        """Return a rotation matrix around the Z axis."""

        radians = math.radians(angle_degrees)
        c = math.cos(radians)
        s = math.sin(radians)

        return Matrix4([
            c, -s, 0.0, 0.0,
            s, c, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ])

    # --------------------------------

    @staticmethod
    def rotation_euler(rotation):
        """Return XYZ Euler rotation matrix in degrees."""

        return (
            Matrix4.rotation_z(rotation.z) @
            Matrix4.rotation_y(rotation.y) @
            Matrix4.rotation_x(rotation.x)
        )

    # --------------------------------

    @staticmethod
    def compose(position=None, rotation=None, scale=None):
        """Compose translation, Euler rotation and scale transforms."""

        position = position or Vector3()
        rotation = rotation or Vector3()
        scale = scale or Vector3(1.0, 1.0, 1.0)

        return (
            Matrix4.translation(position) @
            Matrix4.rotation_euler(rotation) @
            Matrix4.scaling(scale)
        )

    # --------------------------------

    @staticmethod
    def around_pivot(matrix, pivot):
        """Return a transform applied around a world-space pivot."""

        return (
            Matrix4.translation(pivot) @
            matrix @
            Matrix4.translation(Vector3(-pivot.x, -pivot.y, -pivot.z))
        )

    # --------------------------------

    def copy(self):
        """Return a detached matrix copy."""

        return Matrix4(self.values)

    # --------------------------------

    @staticmethod
    def perspective(fov_degrees, aspect, near, far):
        """Return a perspective projection matrix."""

        aspect = max(float(aspect), 0.0001)
        near = max(float(near), 0.0001)
        far = max(float(far), near + 0.0001)
        f = 1.0 / math.tan(math.radians(fov_degrees) / 2.0)

        return Matrix4([
            f / aspect, 0.0, 0.0, 0.0,
            0.0, f, 0.0, 0.0,
            0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far),
            0.0, 0.0, -1.0, 0.0,
        ])

    # --------------------------------

    @staticmethod
    def orthographic(width, height, near, far):
        """Return an orthographic projection matrix."""

        width = max(float(width), 0.0001)
        height = max(float(height), 0.0001)
        near = float(near)
        far = max(float(far), near + 0.0001)

        return Matrix4([
            2.0 / width, 0.0, 0.0, 0.0,
            0.0, 2.0 / height, 0.0, 0.0,
            0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near),
            0.0, 0.0, 0.0, 1.0,
        ])

    # --------------------------------

    @staticmethod
    def look_at(eye, target, up):
        """Return a right-handed look-at view matrix."""

        forward = (target - eye).normalized()
        right = forward.cross(up).normalized()

        if right.length_squared() == 0.0:
            right = Vector3(1.0, 0.0, 0.0)

        true_up = right.cross(forward).normalized()

        return Matrix4([
            right.x, right.y, right.z, -right.dot(eye),
            true_up.x, true_up.y, true_up.z, -true_up.dot(eye),
            -forward.x, -forward.y, -forward.z, forward.dot(eye),
            0.0, 0.0, 0.0, 1.0,
        ])

    # --------------------------------

    def transform_point(self, point):
        """Transform a point and perform perspective divide when needed."""

        x = point.x
        y = point.y
        z = point.z
        m = self.values
        tx = m[0] * x + m[1] * y + m[2] * z + m[3]
        ty = m[4] * x + m[5] * y + m[6] * z + m[7]
        tz = m[8] * x + m[9] * y + m[10] * z + m[11]
        tw = m[12] * x + m[13] * y + m[14] * z + m[15]

        if tw != 0.0:
            tx /= tw
            ty /= tw
            tz /= tw

        return Vector3(tx, ty, tz)

    # --------------------------------

    def __matmul__(self, other):

        result = []

        for row in range(4):
            for column in range(4):
                result.append(sum(
                    self.values[row * 4 + index] * other.values[index * 4 + column]
                    for index in range(4)
                ))

        return Matrix4(result)
