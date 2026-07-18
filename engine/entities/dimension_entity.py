import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QPen, QPolygonF

from engine.dimensions import DimensionStyle
from engine.entities.annotation_helpers import (
    box_from_points,
    copy_entity_metadata,
    point_to_segment_distance,
    text_width,
)
from engine.entities.entity import Entity
from engine.geometry import BoundingBox, Vector2


class BaseDimensionEntity(Entity):
    """Base entity for command-driven, layer-aware dimension annotations."""

    is_dimension = True

    def __init__(self):

        super().__init__()
        self.dimension_style = None
        self.dimension_style_id = None
        self.dimension_style_name = None
        self.text_override = ""

    # --------------------------------

    def draw(self, painter):
        """Draw extension geometry, arrows and dimension text."""

        if not self.visible:
            return

        style = self.effective_style()
        color = "#4fc3f7" if self.selected else self.display_color

        painter.save()
        pen = QPen(QColor(color), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(color))
        self._draw_dimension(painter, style)
        painter.restore()

    # --------------------------------

    def move(self, dx, dy):
        """Move all dimension definition points."""

        for point in self.definition_points():
            point.x += dx
            point.y += dy

    # --------------------------------

    def hit_test(self, point):
        """Return True when a point is near dimension graphics."""

        return any(
            point_to_segment_distance(point, start, end) <= 5.0
            for start, end in self.segments()
        ) or self.bounding_box_contains(point)

    # --------------------------------

    def bounding_box_contains(self, point):
        """Check the dimension bounds with a small pick tolerance."""

        box = self.bounding_box

        return (
            box.min.x - 5.0 <= point.x <= box.max.x + 5.0 and
            box.min.y - 5.0 <= point.y <= box.max.y + 5.0
        )

    # --------------------------------

    def effective_style(self):
        """Return the assigned style or a default fallback style."""

        return self.dimension_style or DimensionStyle()

    # --------------------------------

    def formatted_measurement(self):
        """Return display text for the current measurement."""

        if self.text_override:
            return self.text_override

        style = self.effective_style()

        return f"{self.measurement():.{style.precision}f}"

    # --------------------------------

    def _copy_base_to(self, other):

        copy_entity_metadata(self, other)
        other.dimension_style = self.dimension_style
        other.dimension_style_id = self.dimension_style_id
        other.dimension_style_name = self.dimension_style_name
        other.text_override = self.text_override

    # --------------------------------

    def _draw_text(self, painter, text, position, style):

        painter.save()
        font = QFont()
        font.setPointSizeF(max(1.0, style.text_height))
        painter.setFont(font)
        painter.drawText(QPointF(position.x, position.y), text)
        painter.restore()

    # --------------------------------

    def _draw_arrowhead(self, painter, tip, tail, size):

        direction = tail - tip

        if direction.length() == 0:
            direction = Vector2(1.0, 0.0)

        angle = math.atan2(direction.y, direction.x)
        spread = math.radians(25.0)
        points = [QPointF(tip.x, tip.y)]

        for sign in (-1.0, 1.0):
            theta = angle + sign * spread
            points.append(
                QPointF(
                    tip.x + math.cos(theta) * size,
                    tip.y + math.sin(theta) * size,
                )
            )

        painter.drawPolygon(QPolygonF(points))

    # --------------------------------

    def _dimension_text_position(self, start, end, style):

        mid = Vector2((start.x + end.x) * 0.5, (start.y + end.y) * 0.5)
        text = self.formatted_measurement()

        return Vector2(
            mid.x - text_width(text, style.text_height) * 0.5,
            mid.y - style.text_gap,
        )

    # --------------------------------

    def _bounds_from_points_and_text(self, points):

        box = box_from_points(points)
        style = self.effective_style()
        text = self.formatted_measurement()
        pos = self.text_position(style)
        box.add(pos)
        box.add(Vector2(pos.x + text_width(text, style.text_height), pos.y + style.text_height))

        return box


class LinearDimensionEntity(BaseDimensionEntity):
    """Horizontal or vertical linear dimension."""

    def __init__(self, point1=None, point2=None, dimension_point=None):

        super().__init__()
        self.point1 = point1 or Vector2()
        self.point2 = point2 or Vector2(100.0, 0.0)
        self.dimension_point = dimension_point or Vector2(0.0, 40.0)

    # --------------------------------

    def clone(self):
        """Return an independent copy of this dimension."""

        obj = LinearDimensionEntity(
            self.point1.copy(),
            self.point2.copy(),
            self.dimension_point.copy(),
        )
        self._copy_base_to(obj)

        return obj

    # --------------------------------

    def measurement(self):

        if abs(self.point2.x - self.point1.x) >= abs(self.point2.y - self.point1.y):
            return abs(self.point2.x - self.point1.x)

        return abs(self.point2.y - self.point1.y)

    # --------------------------------

    def definition_points(self):

        return [self.point1, self.point2, self.dimension_point]

    # --------------------------------

    def geometry(self, style=None):

        if abs(self.point2.x - self.point1.x) >= abs(self.point2.y - self.point1.y):
            start = Vector2(self.point1.x, self.dimension_point.y)
            end = Vector2(self.point2.x, self.dimension_point.y)
        else:
            start = Vector2(self.dimension_point.x, self.point1.y)
            end = Vector2(self.dimension_point.x, self.point2.y)

        return start, end

    # --------------------------------

    def segments(self):

        start, end = self.geometry()

        return [(self.point1, start), (self.point2, end), (start, end)]

    # --------------------------------

    def text_position(self, style):

        start, end = self.geometry(style)

        return self._dimension_text_position(start, end, style)

    # --------------------------------

    def _draw_dimension(self, painter, style):

        start, end = self.geometry(style)
        painter.drawLine(QPointF(self.point1.x, self.point1.y), QPointF(start.x, start.y))
        painter.drawLine(QPointF(self.point2.x, self.point2.y), QPointF(end.x, end.y))
        painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))
        self._draw_arrowhead(painter, start, end, style.arrow_size)
        self._draw_arrowhead(painter, end, start, style.arrow_size)
        self._draw_text(painter, self.formatted_measurement(), self.text_position(style), style)

    # --------------------------------

    @property
    def bounding_box(self):

        start, end = self.geometry()

        return self._bounds_from_points_and_text([self.point1, self.point2, start, end])


class AlignedDimensionEntity(BaseDimensionEntity):
    """Dimension aligned with the measured two-point segment."""

    def __init__(self, point1=None, point2=None, dimension_point=None):

        super().__init__()
        self.point1 = point1 or Vector2()
        self.point2 = point2 or Vector2(100.0, 0.0)
        self.dimension_point = dimension_point or Vector2(0.0, 40.0)

    # --------------------------------

    def clone(self):
        """Return an independent copy of this dimension."""

        obj = AlignedDimensionEntity(
            self.point1.copy(),
            self.point2.copy(),
            self.dimension_point.copy(),
        )
        self._copy_base_to(obj)

        return obj

    # --------------------------------

    def measurement(self):

        return self.point1.distance_to(self.point2)

    # --------------------------------

    def definition_points(self):

        return [self.point1, self.point2, self.dimension_point]

    # --------------------------------

    def geometry(self, style=None):

        direction = self.point2 - self.point1

        if direction.length() == 0:
            normal = Vector2(0.0, 1.0)
        else:
            unit = direction.normalized()
            normal = Vector2(-unit.y, unit.x)

        offset = (
            (self.dimension_point.x - self.point1.x) * normal.x +
            (self.dimension_point.y - self.point1.y) * normal.y
        )

        return self.point1 + normal * offset, self.point2 + normal * offset

    # --------------------------------

    def segments(self):

        start, end = self.geometry()

        return [(self.point1, start), (self.point2, end), (start, end)]

    # --------------------------------

    def text_position(self, style):

        start, end = self.geometry(style)

        return self._dimension_text_position(start, end, style)

    # --------------------------------

    def _draw_dimension(self, painter, style):

        start, end = self.geometry(style)
        painter.drawLine(QPointF(self.point1.x, self.point1.y), QPointF(start.x, start.y))
        painter.drawLine(QPointF(self.point2.x, self.point2.y), QPointF(end.x, end.y))
        painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))
        self._draw_arrowhead(painter, start, end, style.arrow_size)
        self._draw_arrowhead(painter, end, start, style.arrow_size)
        self._draw_text(painter, self.formatted_measurement(), self.text_position(style), style)

    # --------------------------------

    @property
    def bounding_box(self):

        start, end = self.geometry()

        return self._bounds_from_points_and_text([self.point1, self.point2, start, end])


class RadiusDimensionEntity(BaseDimensionEntity):
    """Radial dimension from center to radius point."""

    def __init__(self, center=None, radius_point=None, text_point=None):

        super().__init__()
        self.center = center or Vector2()
        self.radius_point = radius_point or Vector2(50.0, 0.0)
        self.text_point = text_point or self.radius_point.copy()

    # --------------------------------

    def clone(self):
        """Return an independent copy of this dimension."""

        obj = RadiusDimensionEntity(
            self.center.copy(),
            self.radius_point.copy(),
            self.text_point.copy(),
        )
        self._copy_base_to(obj)

        return obj

    # --------------------------------

    def measurement(self):

        return self.center.distance_to(self.radius_point)

    # --------------------------------

    def formatted_measurement(self):

        if self.text_override:
            return self.text_override

        style = self.effective_style()

        return f"R{self.measurement():.{style.precision}f}"

    # --------------------------------

    def definition_points(self):

        return [self.center, self.radius_point, self.text_point]

    # --------------------------------

    def segments(self):

        return [(self.center, self.radius_point)]

    # --------------------------------

    def text_position(self, style):

        return Vector2(self.text_point.x + style.text_gap, self.text_point.y - style.text_gap)

    # --------------------------------

    def _draw_dimension(self, painter, style):

        painter.drawLine(
            QPointF(self.center.x, self.center.y),
            QPointF(self.radius_point.x, self.radius_point.y),
        )
        self._draw_arrowhead(painter, self.radius_point, self.center, style.arrow_size)
        self._draw_text(painter, self.formatted_measurement(), self.text_position(style), style)

    # --------------------------------

    @property
    def bounding_box(self):

        return self._bounds_from_points_and_text([self.center, self.radius_point, self.text_point])


class DiameterDimensionEntity(RadiusDimensionEntity):
    """Diameter dimension across a circle through a picked radius point."""

    def clone(self):
        """Return an independent copy of this dimension."""

        obj = DiameterDimensionEntity(
            self.center.copy(),
            self.radius_point.copy(),
            self.text_point.copy(),
        )
        self._copy_base_to(obj)

        return obj

    # --------------------------------

    def measurement(self):

        return self.center.distance_to(self.radius_point) * 2.0

    # --------------------------------

    def formatted_measurement(self):

        if self.text_override:
            return self.text_override

        style = self.effective_style()

        return f"Ø{self.measurement():.{style.precision}f}"

    # --------------------------------

    def opposite_point(self):

        return Vector2(
            self.center.x - (self.radius_point.x - self.center.x),
            self.center.y - (self.radius_point.y - self.center.y),
        )

    # --------------------------------

    def segments(self):

        return [(self.opposite_point(), self.radius_point)]

    # --------------------------------

    def _draw_dimension(self, painter, style):

        opposite = self.opposite_point()
        painter.drawLine(
            QPointF(opposite.x, opposite.y),
            QPointF(self.radius_point.x, self.radius_point.y),
        )
        self._draw_arrowhead(painter, self.radius_point, self.center, style.arrow_size)
        self._draw_arrowhead(painter, opposite, self.center, style.arrow_size)
        self._draw_text(painter, self.formatted_measurement(), self.text_position(style), style)

    # --------------------------------

    @property
    def bounding_box(self):

        return self._bounds_from_points_and_text(
            [self.center, self.radius_point, self.opposite_point(), self.text_point]
        )


class AngularDimensionEntity(BaseDimensionEntity):
    """Angular dimension between two rays sharing a vertex."""

    def __init__(self, vertex=None, point1=None, point2=None, arc_point=None):

        super().__init__()
        self.vertex = vertex or Vector2()
        self.point1 = point1 or Vector2(50.0, 0.0)
        self.point2 = point2 or Vector2(0.0, 50.0)
        self.arc_point = arc_point or Vector2(35.0, 35.0)

    # --------------------------------

    def clone(self):
        """Return an independent copy of this dimension."""

        obj = AngularDimensionEntity(
            self.vertex.copy(),
            self.point1.copy(),
            self.point2.copy(),
            self.arc_point.copy(),
        )
        self._copy_base_to(obj)

        return obj

    # --------------------------------

    def measurement(self):

        start = self._angle_to(self.point1)
        end = self._angle_to(self.point2)
        delta = (end - start) % 360.0

        if delta > 180.0:
            delta = 360.0 - delta

        return delta

    # --------------------------------

    def formatted_measurement(self):

        if self.text_override:
            return self.text_override

        style = self.effective_style()

        return f"{self.measurement():.{style.precision}f}°"

    # --------------------------------

    def definition_points(self):

        return [self.vertex, self.point1, self.point2, self.arc_point]

    # --------------------------------

    def segments(self):

        return [(self.vertex, self.point1), (self.vertex, self.point2)]

    # --------------------------------

    def text_position(self, style):

        return Vector2(self.arc_point.x + style.text_gap, self.arc_point.y - style.text_gap)

    # --------------------------------

    def _draw_dimension(self, painter, style):

        painter.drawLine(QPointF(self.vertex.x, self.vertex.y), QPointF(self.point1.x, self.point1.y))
        painter.drawLine(QPointF(self.vertex.x, self.vertex.y), QPointF(self.point2.x, self.point2.y))

        radius = max(self.vertex.distance_to(self.arc_point), style.arrow_size * 2.0)
        start = self._angle_to(self.point1)
        end = self._angle_to(self.point2)
        span = (end - start) % 360.0

        if span > 180.0:
            span -= 360.0

        rect = QRectF(
            self.vertex.x - radius,
            self.vertex.y - radius,
            radius * 2.0,
            radius * 2.0,
        )
        painter.drawArc(rect, int(-start * 16), int(-span * 16))
        self._draw_text(painter, self.formatted_measurement(), self.text_position(style), style)

    # --------------------------------

    def _angle_to(self, point):

        return math.degrees(math.atan2(point.y - self.vertex.y, point.x - self.vertex.x))

    # --------------------------------

    @property
    def bounding_box(self):

        radius = max(self.vertex.distance_to(self.arc_point), self.effective_style().arrow_size * 2.0)
        box = BoundingBox()
        box.add(Vector2(self.vertex.x - radius, self.vertex.y - radius))
        box.add(Vector2(self.vertex.x + radius, self.vertex.y + radius))
        text = self.text_position(self.effective_style())
        box.add(text)

        return box
