from engine.commands import AddEntityCommand
from engine.entities import MTextEntity
from engine.geometry import Vector2
from engine.tools.tool import Tool


class MTextTool(Tool):
    """Create bounded multi-line text annotations from two picked corners."""

    def __init__(self):

        super().__init__()
        self.start = None
        self.preview = None

    # --------------------------------

    def deactivate(self):

        self.start = None
        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        p = Vector2(point.x, point.y)

        if self.start is None:
            self.start = p
            return

        mtext = self._entity_from_points(self.start, p)
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, mtext))
        self.deactivate()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.start is None:
            return

        self.preview = self._entity_from_points(self.start, Vector2(point.x, point.y))

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

    # --------------------------------

    def _entity_from_points(self, p1, p2):

        position = Vector2(min(p1.x, p2.x), min(p1.y, p2.y))
        width = max(abs(p2.x - p1.x), 20.0)
        height = max(abs(p2.y - p1.y), 20.0)

        return MTextEntity(position, "MText", width, height)
