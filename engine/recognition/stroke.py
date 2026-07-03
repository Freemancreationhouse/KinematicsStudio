from engine.geometry.point import Point


class Stroke:

    def __init__(self):

        self.points = []

    # ----------------------------------

    def add(self, x, y):

        self.points.append(Point(x, y))

    # ----------------------------------

    def clear(self):

        self.points.clear()

    # ----------------------------------

    def count(self):

        return len(self.points)

    # ----------------------------------

    def first(self):

        if self.points:
            return self.points[0]

        return None

    # ----------------------------------

    def last(self):

        if self.points:
            return self.points[-1]

        return None

    # ----------------------------------

    def is_closed(self, tolerance=20):

        if len(self.points) < 5:
            return False

        p1 = self.first()
        p2 = self.last()

        dx = p2.x - p1.x
        dy = p2.y - p1.y

        return (dx * dx + dy * dy) <= tolerance * tolerance