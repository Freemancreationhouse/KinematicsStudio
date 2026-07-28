from math import pi

from engine.entities.entity import Entity
from engine.geometry import Vector2, BoundingBox
from engine.geometry.curves import arc_points, clockwise_span, counter_clockwise_span, point_on_circle
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPen


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
        self.clockwise = False

    # --------------------------------

    def draw(self, painter):

        if not self.visible:
            return

        rect = QRectF(
            self.center.x - self.radius,
            self.center.y - self.radius,
            self.radius * 2.0,
            self.radius * 2.0
        )
        span = self.sweep_angle

        painter.save()
        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawArc(rect, int(-self.start_angle * 16), int(-span * 16))
        painter.restore()

    # --------------------------------

    def move(self, dx, dy):

        self.center.x += dx
        self.center.y += dy

    # --------------------------------

    def clone(self):

        clone = ArcEntity(

            self.center.copy(),

            self.radius,

            self.start_angle,

            self.end_angle

        )
        clone.clockwise = self.clockwise
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

        if self.radius <= 0:
            return False

        return any(
            start.distance_to(point) <= 5.0 or _segment_distance(point, start, end) <= 5.0
            for start, end in zip(self.sampled_points(), self.sampled_points()[1:])
        )

    # --------------------------------

    @property
    def length(self):

        return abs(self.sweep_angle) * pi / 180.0 * self.radius

    # --------------------------------

    @property
    def sweep_angle(self):
        """Return signed sweep angle."""

        return clockwise_span(self.start_angle, self.end_angle) if self.clockwise else counter_clockwise_span(self.start_angle, self.end_angle)

    # --------------------------------

    @property
    def diameter(self):
        """Return arc diameter."""

        return self.radius * 2.0

    # --------------------------------

    @property
    def start_point(self):
        """Return arc start point."""

        return point_on_circle(self.center, self.radius, self.start_angle)

    # --------------------------------

    @property
    def end_point(self):
        """Return arc end point."""

        return point_on_circle(self.center, self.radius, self.end_angle)

    # --------------------------------

    def sampled_points(self):
        """Return sampled points along the arc for snapping and export."""

        return arc_points(
            self.center,
            self.radius,
            self.start_angle,
            self.end_angle,
            self.clockwise,
        )

    # --------------------------------

    @property
    def bounding_box(self):

        box = BoundingBox()

        for point in self.sampled_points():
            box.add(point)

        return box


def _segment_distance(point, start, end):
    """Return point to segment distance without duplicating entity logic."""

    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        return point.distance_to(start)

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    nearest = Vector2(start.x + t * dx, start.y + t * dy)

    return point.distance_to(nearest)
