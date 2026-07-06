from engine.tools.tool import Tool
from engine.commands import MoveEntityCommand


class MoveTool(Tool):

    def __init__(self):

        super().__init__()

        self.entities = []
        self.last = None
        self.total_dx = 0.0
        self.total_dy = 0.0
        self.moving = False

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point):

        if workspace is None:
            return

        self.last = point
        self.total_dx = 0.0
        self.total_dy = 0.0
        self.moving = False

        selection = getattr(workspace, "selection", None)
        selected = list(selection.selected) if selection else []

        candidates = (
            workspace.selectable_entities()
            if hasattr(workspace, "selectable_entities")
            else workspace.entities
        )
        selected = [
            entity for entity in selected
            if entity in candidates
        ]

        for entity in reversed(candidates):

            if entity.hit_test(point):

                if selected and entity in selected:
                    self.entities = selected
                else:
                    if selection:
                        selection.select(entity)
                    self.entities = [entity]

                self.moving = True
                return

        self.entities = []

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.moving or not self.entities:

            return

        dx = point.x - self.last.x
        dy = point.y - self.last.y

        for entity in self.entities:

            entity.move(dx, dy)

        self.last = point
        self.total_dx += dx
        self.total_dy += dy

    # --------------------------------

    def mouse_release(self, workspace, point):

        if (
            workspace is not None and
            self.entities and
            (self.total_dx != 0.0 or self.total_dy != 0.0)
        ):

            workspace.command_manager.record(

                MoveEntityCommand(

                    list(self.entities),

                    self.total_dx,

                    self.total_dy

                )

            )

        self.entities = []
        self.last = None
        self.total_dx = 0.0
        self.total_dy = 0.0
        self.moving = False

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()

    # --------------------------------

    def cancel(self):

        if self.entities and (self.total_dx != 0.0 or self.total_dy != 0.0):

            for entity in self.entities:

                entity.move(-self.total_dx, -self.total_dy)

        self.entities = []
        self.last = None
        self.total_dx = 0.0
        self.total_dy = 0.0
        self.moving = False
