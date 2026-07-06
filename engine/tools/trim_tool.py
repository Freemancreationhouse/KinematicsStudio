from engine.commands import TrimEntityCommand
from engine.geometry.trim import preview_trim, trim_entities
from engine.tools.tool import Tool


class TrimTool(Tool):
    """Two-step trim tool using the V2 workspace and command systems."""

    def __init__(self):

        super().__init__()

        self.cutter = None
        self.target = None
        self.preview = []
        self.pick_point = None
        self.status_text = "Trim: Select cutting edge"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point):

        entity = self._hit(workspace, point, self.cutter)

        if entity is None:
            return

        if self.cutter is None:
            self.cutter = entity
            self.status_text = "Trim: Select entity to trim"
            return

        if entity is self.cutter:
            self.cancel()
            return

        replacements = trim_entities(entity, self.cutter, point)

        if not replacements:
            self.status_text = "Trim: No trim available"
            self.preview = []
            return

        workspace.command_manager.execute(
            TrimEntityCommand(workspace, entity, replacements)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        self.pick_point = point

        if self.cutter is None:
            return

        entity = self._hit(workspace, point, self.cutter)

        if entity is None or entity is self.cutter:
            self.target = None
            self.preview = []
            return

        self.target = entity
        self.preview = preview_trim(entity, self.cutter, point) or []

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        for entity in self.preview:
            previous = getattr(entity, "selected", False)
            entity.selected = True
            entity.draw(painter)
            entity.selected = previous

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()

    # --------------------------------

    def cancel(self):

        self.cutter = None
        self.target = None
        self.preview = []
        self.pick_point = None
        self.status_text = "Trim: Select cutting edge"

    # --------------------------------

    def _hit(self, workspace, point, exclude=None):

        candidates = (
            workspace.selectable_entities()
            if hasattr(workspace, "selectable_entities")
            else workspace.entities
        )

        best = None
        best_distance = 8.0

        for entity in reversed(candidates):
            if entity is exclude:
                continue

            distance = self._entity_distance(entity, point)

            if distance is not None and distance < best_distance:
                best = entity
                best_distance = distance

        return best

    # --------------------------------

    def _entity_distance(self, entity, point):

        if hasattr(entity, "start") and hasattr(entity, "end"):
            return self._segment_distance(point, entity.start, entity.end)

        if hasattr(entity, "p1") and hasattr(entity, "p2"):
            box = entity.bounding_box

            if (
                box.min.x - 8.0 <= point.x <= box.max.x + 8.0 and
                box.min.y - 8.0 <= point.y <= box.max.y + 8.0
            ):
                return 0.0

        return None

    # --------------------------------

    def _segment_distance(self, point, start, end):

        dx = end.x - start.x
        dy = end.y - start.y
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return point.distance_to(start)

        t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
        t = max(0.0, min(1.0, t))

        from engine.geometry import Vector2

        nearest = Vector2(start.x + t * dx, start.y + t * dy)

        return point.distance_to(nearest)
