from engine.entities.entity import Entity
from engine.geometry import BoundingBox
from engine.geometry.curves import (
    clone_points,
    curve_bounds,
    curve_length,
    hit_curve,
    polyline_segments,
)
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen


class PolylineEntity(Entity):
    """Open or closed multi-vertex polyline curve entity."""

    is_curve = True

    def __init__(self, points=None, closed=False):
        super().__init__()
        self.points = clone_points(points)
        self.closed = bool(closed)

    # --------------------------------

    def draw(self, painter):
        """Draw polyline segments using layer-aware color."""

        if not self.visible or len(self.points) < 2:
            return

        painter.save()
        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        for start, end in self.segments():
            painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))

        painter.restore()

    # --------------------------------

    def add_point(self, point):
        """Append a vertex to the polyline."""

        self.points.append(point.copy())

    # --------------------------------

    def add_vertex(self, point, index=None):
        """Add a vertex at an optional index."""

        if index is None:
            self.points.append(point.copy())
        else:
            self.points.insert(max(0, min(index, len(self.points))), point.copy())

    # --------------------------------

    def remove_vertex(self, index):
        """Remove a vertex by index."""

        if 0 <= index < len(self.points):
            return self.points.pop(index)

        return None

    # --------------------------------

    def move_vertex(self, index, point):
        """Move one vertex to a new position."""

        if 0 <= index < len(self.points):
            self.points[index] = point.copy()
            return True

        return False

    # --------------------------------

    def move(self, dx, dy):
        """Move every polyline vertex."""

        for p in self.points:
            p.x += dx
            p.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent copy of this polyline."""

        clone = PolylineEntity(self.points, self.closed)
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
        """Return True when a point is near the curve."""

        return hit_curve(point, self.points, self.closed)

    # --------------------------------

    def segments(self):
        """Return visible polyline segment pairs."""

        return polyline_segments(self.points, self.closed)

    # --------------------------------

    @property
    def length(self):
        """Return the total segment length."""

        return curve_length(self.points, self.closed)

    # --------------------------------

    @property
    def bounding_box(self):
        """Return bounds of all vertices."""

        if not self.points:
            return BoundingBox()

        return curve_bounds(self.points)

    # --------------------------------

    @property
    def count(self):

        return len(self.points)
