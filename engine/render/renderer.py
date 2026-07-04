# CODEX TEST

from PySide6.QtCore import QLineF
from PySide6.QtGui import QColor, QPen


class Renderer:

    def __init__(self):

        self.grid = True
        self.grid_size = 25
        self.camera = None

    # ------------------------------------------------

    def draw_grid(self, painter, width, height):

        if not self.grid:
            return

        painter.setPen(QPen(QColor(55, 55, 55), 1))

        spacing = float(self.grid_size)
        offset_x = 0.0
        offset_y = 0.0

        if self.camera is not None:
            spacing *= self.camera.zoom

        # Avoid excessive painting when zoomed far out.
        while spacing < 8.0:
            spacing *= 5.0

        if self.camera is not None:
            offset_x = (-self.camera.position.x * self.camera.zoom) % spacing
            offset_y = (-self.camera.position.y * self.camera.zoom) % spacing

        # Vertical

        x = offset_x % spacing

        while x <= width:

            painter.drawLine(QLineF(x, 0, x, height))

            x += spacing

        # Horizontal

        y = offset_y % spacing

        while y <= height:

            painter.drawLine(QLineF(0, y, width, y))

            y += spacing

    # ------------------------------------------------

    def draw_entities(self, painter, workspace):

        for entity in tuple(workspace.entities):

            if getattr(entity, "visible", True):
                entity.draw(painter)

    # ------------------------------------------------

    def draw_preview(self, painter, tool):

        if tool:

            tool.draw_preview(painter)

    # ------------------------------------------------

    def render(self, painter, workspace, tool, width, height):
        painter.save()

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

        painter.restore()
