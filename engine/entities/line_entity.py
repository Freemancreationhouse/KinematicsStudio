from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen


class LineEntity(Entity):

    def __init__(self, start=None, end=None):

        super().__init__()

        self.start = start or Vector2()
        self.end = end or Vector2()

    # --------------------------------

    def draw(self, painter):
        if not self.visible:
            return

        painter.save()
        pen = QPen(QColor("#4fc3f7" if self.selected else "#e0e0e0"), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(self.start.x, self.start.y),
            QPointF(self.end.x, self.end.y),
        )
        painter.restore()

    # --------------------------------

    def move(self, dx, dy):

        self.start.x += dx
        self.start.y += dy

        self.end.x += dx
        self.end.y += dy

    # --------------------------------

    def clone(self):

        return LineEntity(

            self.start.copy(),

            self.end.copy()

        )

    # --------------------------------

    def hit_test(self, point):
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return self.start.distance_to(point) <= 5.0

        t = ((point.x - self.start.x) * dx +
             (point.y - self.start.y) * dy) / length_squared
        t = max(0.0, min(1.0, t))
        nearest = Vector2(self.start.x + t * dx, self.start.y + t * dy)

        return nearest.distance_to(point) <= 5.0

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        box.add(self.start)

        box.add(self.end)

        return box
