import math

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QBrush, QPainterPath, QPen, QPolygonF

from engine.entities.annotation_helpers import copy_entity_metadata
from engine.entities.entity import Entity
from engine.geometry import BoundingBox, Vector2
from engine.geometry.hatch import (
    boundary_points_from_entity,
    point_in_polygon,
    polygon_bounds,
    polygon_segments,
)
from engine.geometry.primitives import point_to_segment_distance
from engine.patterns import Pattern


class HatchEntity(Entity):
    """Associative or standalone hatch annotation inside a closed boundary."""

    is_hatch = True

    def __init__(
        self,
        boundary_points=None,
        boundary_entities=None,
        pattern_name="SOLID",
        pattern_scale=10.0,
        pattern_angle=45.0,
    ):

        super().__init__()

        self.boundary_points = [point.copy() for point in (boundary_points or [])]
        self.boundary_entities = list(boundary_entities or [])
        self.boundary_entity_ids = [id(entity) for entity in self.boundary_entities]
        self.pattern = None
        self.pattern_name = pattern_name
        self.pattern_scale = float(pattern_scale)
        self.pattern_angle = float(pattern_angle)
        self.associative = bool(self.boundary_entities)

    # --------------------------------

    def draw(self, painter):
        """Render solid or line-pattern hatch fill."""

        if not self.visible:
            return

        points = self.current_boundary_points()

        if len(points) < 3:
            return

        painter.save()
        color = QColor("#4fc3f7" if self.selected else self.display_color)
        polygon = QPolygonF([QPointF(point.x, point.y) for point in points])
        path = QPainterPath()
        path.addPolygon(polygon)

        if self._is_solid():
            fill = QColor(color)
            fill.setAlpha(70)
            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.drawPolygon(polygon)
        else:
            painter.setClipPath(path)
            self._draw_pattern_lines(painter, points, color)

        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 1)
        pen.setCosmetic(True)
        painter.setClipping(False)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        painter.drawPolygon(polygon)
        painter.restore()

    # --------------------------------

    def move(self, dx, dy):
        """Move standalone hatch points while preserving associative references."""

        if self.associative:
            return

        for point in self.boundary_points:
            point.x += dx
            point.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent hatch entity preserving associations."""

        obj = HatchEntity(
            [point.copy() for point in self.boundary_points],
            list(self.boundary_entities),
            self.pattern_name,
            self.pattern_scale,
            self.pattern_angle,
        )
        obj.pattern = self.pattern
        obj.associative = self.associative
        copy_entity_metadata(self, obj)

        return obj

    # --------------------------------

    def hit_test(self, point):
        """Return True when point is inside or near the hatch boundary."""

        points = self.current_boundary_points()

        if point_in_polygon(point, points):
            return True

        return any(
            point_to_segment_distance(point, start, end) <= 5.0
            for start, end in polygon_segments(points)
        )

    # --------------------------------

    def current_boundary_points(self):
        """Return live associative boundary points or stored fallback points."""

        for entity in list(self.boundary_entities):
            points = boundary_points_from_entity(entity)

            if len(points) >= 3:
                return points

        return [point.copy() for point in self.boundary_points]

    # --------------------------------

    def _is_solid(self):

        pattern = self.pattern or Pattern(self.pattern_name)

        return self.pattern_name.upper() == "SOLID" or pattern.is_solid

    # --------------------------------

    def _draw_pattern_lines(self, painter, points, color):

        bounds = polygon_bounds(points)
        center = bounds.center
        diagonal = max(bounds.width, bounds.height) * 2.0 + self.pattern_scale * 4.0
        spacing = max(1.0, self.pattern_scale)
        radians = math.radians(self.pattern_angle)
        direction = Vector2(math.cos(radians), math.sin(radians))
        normal = Vector2(-direction.y, direction.x)
        pen = QPen(color, 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        offset = -diagonal

        while offset <= diagonal:
            base = center + normal * offset
            start = base - direction * diagonal
            end = base + direction * diagonal
            painter.drawLine(QPointF(start.x, start.y), QPointF(end.x, end.y))
            offset += spacing

    # --------------------------------

    @property
    def bounding_box(self):
        """Return world-space hatch bounds from the live boundary."""

        points = self.current_boundary_points()

        if points:
            return polygon_bounds(points)

        return BoundingBox()
