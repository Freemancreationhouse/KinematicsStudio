from engine.tools.tool import Tool
from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.commands import AddEntityCommand


class LineTool(Tool):

    def __init__(self):

        super().__init__()

        self.start = None
        self.preview = None

    def deactivate(self):

        self.start = None
        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        p = Vector2(point.x, point.y)

        if self.start is None:

            self.start = p

        else:

            line = LineEntity(

                self.start.copy(),

                p.copy()

            )

            workspace.command_manager.execute(

                AddEntityCommand(workspace.entities, line)

            )

            self.start = None

            self.preview = None

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.start is None:

            return

        self.preview = LineEntity(

            self.start.copy(),

            Vector2(point.x, point.y)

        )

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:

            self.preview.draw(painter)

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
