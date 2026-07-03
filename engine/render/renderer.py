from PySide6.QtGui import QColor, QPen


class Renderer:

    def __init__(self):

        self.grid = True
        self.grid_size = 25

    # ------------------------------------------------

    def draw_grid(self, painter, width, height):

        if not self.grid:
            return

        painter.setPen(QPen(QColor(55, 55, 55), 1))

        # Vertical

        x = 0

        while x <= width:

            painter.drawLine(x, 0, x, height)

            x += self.grid_size

        # Horizontal

        y = 0

        while y <= height:

            painter.drawLine(0, y, width, y)

            y += self.grid_size

    # ------------------------------------------------

    def draw_entities(self, painter, workspace):

        for entity in workspace.entities:

            entity.draw(painter)

    # ------------------------------------------------

    def draw_preview(self, painter, tool):

        if tool:

            tool.draw_preview(painter)

    # ------------------------------------------------

    def render(self, painter, workspace, tool, width, height):

        self.draw_grid(

            painter,

            width,

            height

        )

        self.draw_entities(

            painter,

            workspace

        )

        self.draw_preview(

            painter,

            tool

        )