from math import pi

from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox


class ArcEntity(Entity):

    def __init__(

        self,

        center=None,

        radius=0,

        start_angle=0,

        end_angle=90

    ):

        super().__init__()

        self.center = center or Vector2()

        self.radius = float(radius)

        self.start_angle = float(start_angle)

        self.end_angle = float(end_angle)

    # --------------------------------

    def draw(self, painter):

        pass

    # --------------------------------

    def move(self, dx, dy):

        self.center.x += dx
        self.center.y += dy

    # --------------------------------

    def clone(self):

        return ArcEntity(

            self.center.copy(),

            self.radius,

            self.start_angle,

            self.end_angle

        )

    # --------------------------------

    def hit_test(self, point):

        return False

    # --------------------------------

    @property
    def length(self):

        return (

            abs(self.end_angle - self.start_angle)

            * pi

            / 180

        ) * self.radius

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