from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen

from engine.entities.entity import Entity
from engine.geometry import BoundingBox
from engine.geometry.curves import (
    catmull_rom_points,
    clone_points,
    curve_bounds,
    curve_length,
    hit_curve,
    polyline_segments,
)


class SplineEntity(Entity):
    """Interpolated spline curve defined by editable control points."""

    is_curve = True

    def __init__(self, control_points=None, samples_per_segment=16):

        super().__init__()
        self.control_points = clone_points(control_points)
        self.samples_per_segment = int(samples_per_segment or 16)

    # --------------------------------

    def draw(self, painter):
        """Draw interpolated spline segments."""

        samples = self.sampled_points()

        if not self.visible or len(samples) < 2:
            return

        painter.save()
        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)

        for start, end in polyline_segments(samples):
            painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))

        painter.restore()

    # --------------------------------

    def add_control_point(self, point, index=None):
        """Add a control point at an optional index."""

        if index is None:
            self.control_points.append(point.copy())
        else:
            self.control_points.insert(max(0, min(index, len(self.control_points))), point.copy())

    # --------------------------------

    def remove_control_point(self, index):
        """Remove a control point by index."""

        if 0 <= index < len(self.control_points):
            return self.control_points.pop(index)

        return None

    # --------------------------------

    def move_control_point(self, index, point):
        """Move one control point to a new position."""

        if 0 <= index < len(self.control_points):
            self.control_points[index] = point.copy()
            return True

        return False

    # --------------------------------

    def move(self, dx, dy):
        """Move every control point."""

        for point in self.control_points:
            point.x += dx
            point.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent copy of this spline."""

        clone = SplineEntity(self.control_points, self.samples_per_segment)
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
        """Return True when a point is near the sampled spline."""

        return hit_curve(point, self.sampled_points())

    # --------------------------------

    def sampled_points(self):
        """Return interpolated display points."""

        return catmull_rom_points(self.control_points, self.samples_per_segment)

    # --------------------------------

    @property
    def length(self):
        """Return approximate spline length."""

        return curve_length(self.sampled_points())

    # --------------------------------

    @property
    def bounding_box(self):
        """Return bounds of sampled spline points."""

        samples = self.sampled_points()

        if not samples:
            return BoundingBox()

        return curve_bounds(samples)

    # --------------------------------

    @property
    def count(self):
        """Return control point count."""

        return len(self.control_points)
