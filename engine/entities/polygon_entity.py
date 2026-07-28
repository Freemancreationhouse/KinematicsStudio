from math import sin, pi

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen

from engine.entities.entity import Entity
from engine.geometry import BoundingBox, Vector2
from engine.geometry.curves import (
    polygon_area,
    polygon_perimeter,
    regular_polygon_points,
)


class PolygonEntity(Entity):
    """Editable regular polygon entity for the 2D CAD workspace."""

    def __init__(self, center=None, radius=0.0, sides=6, rotation=0.0, mode="Inscribed"):
        super().__init__()
        self.center = center or Vector2()
        self.radius = abs(float(radius))
        self.sides = max(3, min(360, int(sides)))
        self.rotation = float(rotation)
        self.mode = str(mode or "Inscribed")

    # --------------------------------

    def draw(self, painter):
        """Draw regular polygon edges."""

        if not self.visible:
            return

        points = self.points

        if len(points) < 3:
            return

        painter.save()
        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))

        for start, end in zip(points, points[1:] + points[:1]):
            painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))

        painter.restore()

    # --------------------------------

    def move(self, dx, dy):
        """Translate the polygon center."""

        self.center.x += dx
        self.center.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent polygon copy."""

        clone = PolygonEntity(
            self.center.copy(),
            self.radius,
            self.sides,
            self.rotation,
            self.mode,
        )
        clone.selected = self.selected
        clone.visible = self.visible
        clone.locked = self.locked
        clone.layer = self.layer
        clone.layer_id = self.layer_id
        clone.layer_name = self.layer_name
        clone.color = self.color

        return clone

    # --------------------------------

    def hit_test(self, point):
        """Return True when point is close to a polygon edge or inside it."""

        points = self.points

        return any(
            _segment_distance(point, start, end) <= 5.0
            for start, end in zip(points, points[1:] + points[:1])
        )

    # --------------------------------

    @property
    def points(self):
        """Return polygon vertices."""

        return regular_polygon_points(self.center, self.radius, self.sides, self.rotation)

    # --------------------------------

    @property
    def edge_length(self):
        """Return side length."""

        if self.sides < 3:
            return 0.0

        return 2.0 * self.radius * sin(pi / self.sides)

    # --------------------------------

    @property
    def area(self):
        """Return polygon area."""

        return polygon_area(self.points)

    # --------------------------------

    @property
    def perimeter(self):
        """Return polygon perimeter."""

        return polygon_perimeter(self.points)

    # --------------------------------

    @property
    def bounding_box(self):
        """Return polygon bounds."""

        box = BoundingBox()

        for point in self.points:
            box.add(point)

        return box


def _segment_distance(point, start, end):
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        return point.distance_to(start)

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    nearest = Vector2(start.x + t * dx, start.y + t * dy)

    return point.distance_to(nearest)
