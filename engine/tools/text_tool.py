from engine.commands import AddEntityCommand
from engine.entities import TextEntity
from engine.geometry import Vector2
from engine.tools.tool import Tool


class TextTool(Tool):
    """Create single-line text annotations at a picked position."""

    def __init__(self):

        super().__init__()
        self.preview = None

    # --------------------------------

    def deactivate(self):

        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        text = TextEntity(Vector2(point.x, point.y), "Text")
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, text))
        self.preview = None

    # --------------------------------

    def mouse_move(self, workspace, point):

        self.preview = TextEntity(Vector2(point.x, point.y), "Text")

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
