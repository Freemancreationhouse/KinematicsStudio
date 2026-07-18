import math

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPen, QPolygonF

from engine.entities.annotation_helpers import (
    DEFAULT_LEADER_TEXT,
    copy_entity_metadata,
    point_to_segment_distance,
)
from engine.entities.entity import Entity
from engine.entities.text_entity import TextEntity
from engine.geometry import BoundingBox, Vector2


class LeaderEntity(Entity):
    """Leader annotation with arrowhead, landing line and attached text."""

    def __init__(
        self,
        arrow_point=None,
        landing_start=None,
        landing_end=None,
        text_entity=None,
    ):

        super().__init__()

        self.arrow_point = arrow_point or Vector2()
        self.landing_start = landing_start or Vector2(self.arrow_point.x + 40.0, self.arrow_point.y + 20.0)
        self.landing_end = landing_end or Vector2(self.landing_start.x + 60.0, self.landing_start.y)
        self.text_entity = text_entity or TextEntity(
            Vector2(self.landing_end.x + 6.0, self.landing_end.y),
            DEFAULT_LEADER_TEXT,
        )

    # --------------------------------

    def draw(self, painter):
        """Draw the leader segments, arrowhead and attached text."""

        if not self.visible:
            return

        color = "#4fc3f7" if self.selected else self.display_color

        painter.save()
        pen = QPen(QColor(color), 2)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(self.arrow_point.x, self.arrow_point.y),
            QPointF(self.landing_start.x, self.landing_start.y),
        )
        painter.drawLine(
            QPointF(self.landing_start.x, self.landing_start.y),
            QPointF(self.landing_end.x, self.landing_end.y),
        )
        painter.setBrush(QColor(color))
        painter.drawPolygon(self._arrowhead_polygon())
        painter.restore()

        self._draw_text(painter)

    # --------------------------------

    def move(self, dx, dy):
        """Move the full leader annotation including attached text."""

        for point in (self.arrow_point, self.landing_start, self.landing_end):
            point.x += dx
            point.y += dy

        self.text_entity.move(dx, dy)

    # --------------------------------

    def clone(self):
        """Return an independent copy of this leader annotation."""

        obj = LeaderEntity(
            self.arrow_point.copy(),
            self.landing_start.copy(),
            self.landing_end.copy(),
            self.text_entity.clone(),
        )
        copy_entity_metadata(self, obj)

        return obj

    # --------------------------------

    def hit_test(self, point):
        """Return True when a point intersects the leader or attached text."""

        return (
            point_to_segment_distance(point, self.arrow_point, self.landing_start) <= 5.0 or
            point_to_segment_distance(point, self.landing_start, self.landing_end) <= 5.0 or
            self.text_entity.hit_test(point)
        )

    # --------------------------------

    def _draw_text(self, painter):

        self.text_entity.selected = self.selected
        self.text_entity.layer = self.layer
        self.text_entity.layer_id = self.layer_id
        self.text_entity.layer_name = self.layer_name
        self.text_entity.color = self.color
        self.text_entity.visible = self.visible
        self.text_entity.draw(painter)

    # --------------------------------

    def _arrowhead_polygon(self):

        direction = self.landing_start - self.arrow_point

        if direction.length() == 0:
            direction = Vector2(1.0, 0.0)

        angle = math.atan2(direction.y, direction.x)
        size = 10.0
        spread = math.radians(25.0)

        points = [QPointF(self.arrow_point.x, self.arrow_point.y)]

        for sign in (-1.0, 1.0):
            theta = angle + math.pi + sign * spread
            points.append(
                QPointF(
                    self.arrow_point.x + math.cos(theta) * size,
                    self.arrow_point.y + math.sin(theta) * size,
                )
            )

        return QPolygonF(points)

    # --------------------------------

    @property
    def bounding_box(self):
        """World-space bounds for the leader segments and attached text."""

        box = BoundingBox()

        for point in (self.arrow_point, self.landing_start, self.landing_end):
            box.add(point)

        text_box = self.text_entity.bounding_box
        box.add(text_box.min)
        box.add(text_box.max)

        return box
