from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QFont, QPen

from engine.entities.annotation_helpers import (
    DEFAULT_MTEXT,
    DEFAULT_TEXT_HEIGHT,
    copy_entity_metadata,
    point_in_local_box,
    rotated_box,
    wrapped_lines,
)
from engine.entities.entity import Entity
from engine.geometry import Vector2


class MTextEntity(Entity):
    """Multi-line text annotation with bounded wrapping and alignment state."""

    def __init__(
        self,
        position=None,
        text=DEFAULT_MTEXT,
        box_width=180.0,
        box_height=80.0,
        height=DEFAULT_TEXT_HEIGHT,
        rotation=0.0,
        alignment="Left",
    ):

        super().__init__()

        self.position = position or Vector2()
        self.text = text
        self.box_width = float(box_width)
        self.box_height = float(box_height)
        self.height = float(height)
        self.rotation = float(rotation)
        self.alignment = alignment or "Left"

    # --------------------------------

    def draw(self, painter):
        """Draw the wrapped text block and its selection outline when selected."""

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

        y = self.height
        for line in self.lines():
            x = self._line_x(line)
            painter.drawText(QPointF(x, y), line)
            y += self.height

        if self.selected:
            painter.drawRect(0.0, 0.0, self.box_width, self.box_height)

        painter.restore()

    # --------------------------------

    def move(self, dx, dy):
        """Move the mtext insertion point."""

        self.position.x += dx
        self.position.y += dy

    # --------------------------------

    def clone(self):
        """Return an independent copy of this mtext entity."""

        obj = MTextEntity(
            self.position.copy(),
            self.text,
            self.box_width,
            self.box_height,
            self.height,
            self.rotation,
            self.alignment,
        )
        copy_entity_metadata(self, obj)

        return obj

    # --------------------------------

    def hit_test(self, point):
        """Return True when a point intersects the mtext bounding box."""

        return point_in_local_box(
            point,
            self.position,
            self.box_width,
            self.box_height,
            self.rotation,
        )

    # --------------------------------

    def lines(self):
        """Return wrapped display lines for the current text and box width."""

        return wrapped_lines(self.text, self.box_width, self.height)

    # --------------------------------

    def _line_x(self, line):

        estimated_width = len(str(line or "")) * max(self.height, 1.0) * 0.6
        alignment = str(self.alignment or "Left").lower()

        if alignment == "center":
            return max(0.0, (self.box_width - estimated_width) * 0.5)

        if alignment == "right":
            return max(0.0, self.box_width - estimated_width)

        return 0.0

    # --------------------------------

    @property
    def bounding_box(self):
        """World-space bounds for rendering, selection and culling."""

        return rotated_box(self.position, self.box_width, self.box_height, self.rotation)
