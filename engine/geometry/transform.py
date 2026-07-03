from math import sin, cos, radians

from engine.geometry.vector import Vector


class Transform:

    @staticmethod
    def translate(point, dx, dy):

        return Vector(

            point.x + dx,

            point.y + dy,

            point.z

        )

    @staticmethod
    def scale(point, sx, sy):

        return Vector(

            point.x * sx,

            point.y * sy,

            point.z

        )

    @staticmethod
    def rotate(point, angle):

        a = radians(angle)

        c = cos(a)
        s = sin(a)

        return Vector(

            point.x * c - point.y * s,

            point.x * s + point.y * c,

            point.z

        )