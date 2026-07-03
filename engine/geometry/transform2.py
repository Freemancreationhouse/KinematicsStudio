from engine.geometry.matrix3 import Matrix3


class Transform2:

    def __init__(self):

        self.matrix = Matrix3()

    # -----------------------------

    def reset(self):

        self.matrix.identity()

        return self

    # -----------------------------

    def translate(self, x, y):

        self.matrix.translate(x, y)

        return self

    # -----------------------------

    def rotate(self, angle):

        self.matrix.rotate(angle)

        return self

    # -----------------------------

    def scale(self, sx, sy):

        self.matrix.scale(sx, sy)

        return self

    # -----------------------------

    def apply(self, point):

        return self.matrix.transform(point)