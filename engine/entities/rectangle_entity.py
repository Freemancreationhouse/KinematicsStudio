from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox


class RectangleEntity(Entity):

    def __init__(self, p1=None, p2=None):

        super().__init__()

        self.p1 = p1 or Vector2()
        self.p2 = p2 or Vector2()

    # --------------------------------

    def draw(self, painter):

        pass

    # --------------------------------

    def move(self, dx, dy):

        self.p1.x += dx
        self.p1.y += dy

        self.p2.x += dx
        self.p2.y += dy

    # --------------------------------

    def clone(self):

        return RectangleEntity(

            self.p1.copy(),

            self.p2.copy()

        )

    # --------------------------------

    def hit_test(self, point):

        return (

            min(self.p1.x, self.p2.x)
            <= point.x <=
            max(self.p1.x, self.p2.x)

            and

            min(self.p1.y, self.p2.y)
            <= point.y <=
            max(self.p1.y, self.p2.y)

        )

    # --------------------------------

    @property
    def width(self):

        return abs(self.p2.x - self.p1.x)

    @property
    def height(self):

        return abs(self.p2.y - self.p1.y)

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        box.add(self.p1)
        box.add(self.p2)

        return box