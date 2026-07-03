from math import cos, sin, radians

from engine.geometry.vector2 import Vector2


class Matrix3:

    def __init__(self):

        self.identity()

    # --------------------------------

    def identity(self):

        self.m = [

            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]

        ]

        return self

    # --------------------------------

    def translate(self, tx, ty):

        self.m = [

            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]

        ]

        return self

    # --------------------------------

    def scale(self, sx, sy):

        self.m = [

            [sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]

        ]

        return self

    # --------------------------------

    def rotate(self, angle):

        a = radians(angle)

        c = cos(a)
        s = sin(a)

        self.m = [

            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]

        ]

        return self

    # --------------------------------

    def transform(self, v):

        x = v.x
        y = v.y

        return Vector2(

            x * self.m[0][0] + y * self.m[0][1] + self.m[0][2],

            x * self.m[1][0] + y * self.m[1][1] + self.m[1][2]

        )