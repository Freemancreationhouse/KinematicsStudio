# CODEX TEST

from PySide6.QtCore import QLineF, QPointF
from PySide6.QtGui import QColor, QFont, QPen


class Renderer:
    """Draws the workspace, view grid, previews, and transient feedback."""

    def __init__(self):

        self.grid = True
        self.grid_size = 25
        self.camera = None
        self._last_width = 0
        self._last_height = 0

    # ------------------------------------------------

    def draw_grid(self, painter, width, height):

        if not self.grid:
            return

        zoom = self.camera.zoom if self.camera is not None else 1.0
        minor_spacing = float(self.grid_size) * zoom

        while minor_spacing < 8.0:
            minor_spacing *= 2.0

        while minor_spacing > 80.0:
            minor_spacing *= 0.5

        if self.camera is not None:
            offset_x = (-self.camera.position.x * zoom) % minor_spacing
            offset_y = (-self.camera.position.y * zoom) % minor_spacing
        else:
            offset_x = 0.0
            offset_y = 0.0

        painter.save()

        minor_pen = QPen(QColor(48, 48, 48), 1)
        major_pen = QPen(QColor(68, 68, 68), 1)
        minor_pen.setCosmetic(True)
        major_pen.setCosmetic(True)

        x = offset_x
        index = 0

        while x <= width:
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(QLineF(x, 0, x, height))
            x += minor_spacing
            index += 1

        y = offset_y
        index = 0

        while y <= height:
            painter.setPen(major_pen if index % 5 == 0 else minor_pen)
            painter.drawLine(QLineF(0, y, width, y))
            y += minor_spacing
            index += 1

        painter.restore()

    # ------------------------------------------------

    def draw_entities(self, painter, workspace):
        visible = (
            workspace.visible_entities()
            if hasattr(workspace, "visible_entities")
            else tuple(workspace.entities)
        )

        for entity in tuple(visible):

            if self._entity_in_view(entity):
                entity.draw(painter)

    # ------------------------------------------------

    def _entity_in_view(self, entity):
        if self.camera is None:
            return True

        box = entity.bounding_box
        view_left = self.camera.position.x
        view_top = self.camera.position.y
        view_right = view_left + self._last_width / self.camera.zoom
        view_bottom = view_top + self._last_height / self.camera.zoom

        return not (
            box.max.x < view_left or
            box.min.x > view_right or
            box.max.y < view_top or
            box.min.y > view_bottom
        )

    # ------------------------------------------------

    def draw_preview(self, painter, tool):

        if tool:

            tool.draw_preview(painter)

    # ------------------------------------------------

    def draw_snap_feedback(self, painter, snap_result):

        if not snap_result or snap_result.mode == "OFF":
            return

        point = snap_result.point

        painter.save()

        if snap_result.entity is not None:
            previous = getattr(snap_result.entity, "selected", False)
            snap_result.entity.selected = True
            snap_result.entity.draw(painter)
            snap_result.entity.selected = previous

        pen = QPen(QColor("#ffeb3b"), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(QColor(255, 235, 59, 80))

        size = 6 / self.camera.zoom if self.camera else 6
        painter.drawLine(
            QLineF(point.x - size, point.y, point.x + size, point.y)
        )
        painter.drawLine(
            QLineF(point.x, point.y - size, point.x, point.y + size)
        )
        painter.drawEllipse(QPointF(point.x, point.y), size, size)

        font = QFont()
        font.setPointSizeF(max(7.0, 9.0 / (self.camera.zoom if self.camera else 1.0)))
        painter.setFont(font)
        painter.drawText(
            QPointF(point.x + size * 1.5, point.y - size * 1.5),
            snap_result.mode
        )

        painter.restore()

    # ------------------------------------------------

    def render(self, painter, workspace, tool, width, height, snap_result=None):
        painter.save()
        self._last_width = width
        self._last_height = height

        self.draw_grid(

            painter,

            width,

            height

        )

        if self.camera is not None:
            painter.translate(-self.camera.position.x * self.camera.zoom,
                              -self.camera.position.y * self.camera.zoom)
            painter.scale(self.camera.zoom, self.camera.zoom)

        self.draw_entities(

            painter,

            workspace

        )

        self.draw_preview(

            painter,

            tool

        )

        self.draw_snap_feedback(painter, snap_result)

        painter.restore()
