from engine.tools.tool import Tool


class MoveTool(Tool):

    def __init__(self):

        super().__init__()

        self.entity = None
        self.last = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        self.last = point

        self.entity = None

        for entity in reversed(workspace.entities):

            if entity.hit_test(point):

                self.entity = entity

                break

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.entity is None:

            return

        dx = point.x - self.last.x
        dy = point.y - self.last.y

        self.entity.move(dx, dy)

        self.last = point

    # --------------------------------

    def mouse_release(self, workspace, point):

        self.entity = None