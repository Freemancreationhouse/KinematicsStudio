from math import pi

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPen

from engine.entities.entity import Entity
from engine.geometry import BoundingBox, Vector2
from engine.geometry.curves import ellipse_perimeter, ellipse_points


class EllipseEntity(Entity):
    """Editable rotated ellipse entity for the 2D CAD workspace."""

    def __init__(self, center=None, radius_x=0.0, radius_y=0.0, rotation=0.0):
        super().__init__()
        self.center = center or Vector2()
        self.radius_x = abs(float(radius_x))
        self.radius_y = abs(float(radius_y))
        self.rotation = float(rotation)

    # --------------------------------

    def draw(self, painter):
        """Draw the ellipse through the read-only renderer path."""

        if not self.visible:
            return

        painter.save()
        painter.translate(self.center.x, self.center.y)
        painter.rotate(self.rotation)
        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawEllipse(
            QRectF(
                -self.radius_x,
                -self.radius_y,
                self.radius_x * 2.0,
                self.radius_y * 2.0,
            )
        )
        painter.restore()

    # --------------------------------

    def move(self, dx, dy):
        """Translate the ellipse center."""

        self.center.x += dx
        self.center.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent ellipse copy."""

        clone = EllipseEntity(
            self.center.copy(),
            self.radius_x,
            self.radius_y,
            self.rotation,
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
        """Return True when point is close to the ellipse perimeter."""

        samples = self.sampled_points()

        return any(
            _segment_distance(point, start, end) <= 5.0
            for start, end in zip(samples, samples[1:] + samples[:1])
        )

    # --------------------------------

    def sampled_points(self):
        """Return sampled points along the ellipse."""

        return ellipse_points(self.center, self.radius_x, self.radius_y, self.rotation)

    # --------------------------------

    @property
    def major_axis(self):
        """Return the major axis diameter."""

        return max(self.radius_x, self.radius_y) * 2.0

    # --------------------------------

    @property
    def minor_axis(self):
        """Return the minor axis diameter."""

        return min(self.radius_x, self.radius_y) * 2.0

    # --------------------------------

    @property
    def area(self):
        """Return ellipse area."""

        return pi * self.radius_x * self.radius_y

    # --------------------------------

    @property
    def perimeter(self):
        """Return approximate ellipse perimeter."""

        return ellipse_perimeter(self.radius_x, self.radius_y)

    # --------------------------------

    @property
    def bounding_box(self):
        """Return sampled bounds for the rotated ellipse."""

        box = BoundingBox()

        for point in self.sampled_points():
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
