from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QFont, QPen

from engine.entities.annotation_helpers import (
    DEFAULT_TEXT,
    DEFAULT_TEXT_HEIGHT,
    copy_entity_metadata,
    normalized_lines,
    point_in_local_box,
    rotated_box,
    text_block_size,
)
from engine.entities.entity import Entity
from engine.geometry import Vector2


class TextEntity(Entity):
    """Single-line text annotation stored and rendered as a workspace entity."""

    def __init__(self, position=None, text=DEFAULT_TEXT, height=DEFAULT_TEXT_HEIGHT, rotation=0.0):

        super().__init__()

        self.position = position or Vector2()
        self.text = text
        self.height = float(height)
        self.rotation = float(rotation)
        self.alignment = "Left"

    # --------------------------------

    def draw(self, painter):
        """Draw the text annotation using its layer-aware display color."""

        if not self.visible:
            return

        painter.save()
        painter.translate(self.position.x, self.position.y)
        painter.rotate(self.rotation)

        pen = QPen(QColor("#4fc3f7" if self.selected else self.display_color), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        font = QFont()
        font.setPointSizeF(max(1.0, self.height))
        painter.setFont(font)
        painter.drawText(QPointF(0.0, self.height), str(self.text or ""))
        painter.restore()

    # --------------------------------

    def move(self, dx, dy):
        """Move the text insertion point."""

        self.position.x += dx
        self.position.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent copy of this text entity."""

        obj = TextEntity(
            self.position.copy(),
            self.text,
            self.height,
            self.rotation,
        )
        obj.alignment = self.alignment
        copy_entity_metadata(self, obj)

        return obj

    # --------------------------------

    def hit_test(self, point):
        """Return True when a point intersects the approximate text bounds."""

        width, height = text_block_size(normalized_lines(self.text), self.height)

        return point_in_local_box(point, self.position, width, height, self.rotation)

    # --------------------------------

    @property
    def bounding_box(self):
        """Approximate world-space bounds for rendering, selection and culling."""

        width, height = text_block_size(normalized_lines(self.text), self.height)

        return rotated_box(self.position, width, height, self.rotation)
