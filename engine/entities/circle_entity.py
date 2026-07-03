from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox


class CircleEntity(Entity):

    def __init__(self, center=None, radius=0):

        super().__init__()

        self.center = center or Vector2()
        self.radius = float(radius)

    # --------------------------------

    def draw(self, painter):

        pass

    # --------------------------------

    def move(self, dx, dy):

        self.center.x += dx
        self.center.y += dy

    # --------------------------------

    def clone(self):

        return CircleEntity(

            self.center.copy(),

            self.radius

        )

    # --------------------------------

    def hit_test(self, point):

        return self.center.distance_to(point) <= self.radius

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        box.add(

            Vector2(

                self.center.x - self.radius,

                self.center.y - self.radius

            )

        )

        box.add(

            Vector2(

                self.center.x + self.radius,

                self.center.y + self.radius

            )

        )

        return box