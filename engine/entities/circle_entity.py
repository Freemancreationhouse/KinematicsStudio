from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen


class CircleEntity(Entity):

    def __init__(self, center=None, radius=0):

        super().__init__()

        self.center = center or Vector2()
        self.radius = float(radius)

    # --------------------------------

    def draw(self, painter):
        if not self.visible:
            return

        painter.save()
        pen = QPen(QColor("#4fc3f7" if self.selected else "#e0e0e0"), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawEllipse(QPointF(self.center.x, self.center.y), self.radius, self.radius)
        painter.restore()

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
