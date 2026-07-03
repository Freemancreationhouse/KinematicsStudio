from math import sqrt


class Vector2:

    def __init__(self, x=0.0, y=0.0):

        self.x = float(x)
        self.y = float(y)

    # --------------------------------

    def copy(self):

        return Vector2(self.x, self.y)

    # --------------------------------

    def length(self):

        return sqrt(self.x * self.x + self.y * self.y)

    # --------------------------------

    def normalized(self):

        l = self.length()

        if l == 0:

            return Vector2()

        return Vector2(

            self.x / l,

            self.y / l

        )

    # --------------------------------

    def distance_to(self, other):

        return sqrt(

            (self.x - other.x) ** 2 +

            (self.y - other.y) ** 2

        )

    # --------------------------------

    def __add__(self, other):

        return Vector2(

            self.x + other.x,

            self.y + other.y

        )

    # --------------------------------

    def __sub__(self, other):

        return Vector2(

            self.x - other.x,

            self.y - other.y

        )

    # --------------------------------

    def __mul__(self, value):

        return Vector2(

            self.x * value,

            self.y * value

        )

    # --------------------------------

    def __repr__(self):

        return f"Vector2({self.x}, {self.y})"