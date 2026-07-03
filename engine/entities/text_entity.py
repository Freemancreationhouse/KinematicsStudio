from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox


class TextEntity(Entity):

    def __init__(self, position=None, text=""):

        super().__init__()

        self.position = position or Vector2()
        self.text = text
        self.height = 20

    # --------------------------------

    def draw(self, painter):

        pass

    # --------------------------------

    def move(self, dx, dy):

        self.position.x += dx
        self.position.y += dy

    # --------------------------------

    def clone(self):

        obj = TextEntity(

            self.position.copy(),

            self.text

        )

        obj.height = self.height

        return obj

    # --------------------------------

    def hit_test(self, point):

        return False

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        width = max(len(self.text), 1) * self.height * 0.6

        box.add(self.position)

        box.add(

            Vector2(

                self.position.x + width,

                self.position.y + self.height

            )

        )

        return box