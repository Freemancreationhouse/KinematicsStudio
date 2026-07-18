from engine.commands import AddEntityCommand
from engine.entities import LeaderEntity, TextEntity
from engine.geometry import Vector2
from engine.tools.tool import Tool


class LeaderTool(Tool):
    """Create leader annotations from an arrow point to a landing line."""

    def __init__(self):

        super().__init__()
        self.arrow_point = None
        self.preview = None

    # --------------------------------

    def deactivate(self):

        self.arrow_point = None
        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        p = Vector2(point.x, point.y)

        if self.arrow_point is None:
            self.arrow_point = p
            return

        leader = self._entity_from_points(self.arrow_point, p)
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, leader))
        self.deactivate()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.arrow_point is None:
            return

        self.preview = self._entity_from_points(self.arrow_point, Vector2(point.x, point.y))

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

    def _entity_from_points(self, arrow_point, landing_end):

        landing_start = Vector2(
            landing_end.x - 60.0 if landing_end.x >= arrow_point.x else landing_end.x + 60.0,
            landing_end.y,
        )
        text_position = Vector2(landing_end.x + 6.0, landing_end.y)
        text = TextEntity(text_position, "Leader")

        return LeaderEntity(arrow_point.copy(), landing_start, landing_end.copy(), text)
