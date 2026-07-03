from math import sqrt

from engine.tools.tool import Tool
from engine.entities import CircleEntity
from engine.geometry import Vector2


class CircleTool(Tool):

    def __init__(self):

        super().__init__()

        self.center = None
        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        p = Vector2(point.x, point.y)

        if self.center is None:

            self.center = p

        else:

            radius = self.center.distance_to(p)

            circle = CircleEntity(

                self.center.copy(),

                radius

            )

            workspace.add_entity(circle)

            self.center = None
            self.preview = None

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.center is None:

            return

        p = Vector2(point.x, point.y)

        radius = self.center.distance_to(p)

        self.preview = CircleEntity(

            self.center.copy(),

            radius

        )

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:

            self.preview.draw(painter)