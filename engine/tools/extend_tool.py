from engine.commands import ExtendEntityCommand
from engine.geometry.extend import extend_entities, preview_extend
from engine.tools.tool import Tool


class ExtendTool(Tool):
    """Two-step extend tool using the V2 workspace and command systems."""

    def __init__(self):

        super().__init__()

        self.boundary = None
        self.target = None
        self.preview = []
        self.pick_point = None
        self.status_text = "Extend: Select boundary edge"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point):

        entity = self._hit(workspace, point, self.boundary)

        if entity is None:
            return

        if self.boundary is None:
            self.boundary = entity
            self.status_text = "Extend: Select entity to extend"
            return

        if entity is self.boundary:
            self.cancel()
            return

        replacements = extend_entities(entity, self.boundary, point)

        if not replacements:
            self.status_text = "Extend: No extension available"
            self.preview = []
            return

        workspace.command_manager.execute(
            ExtendEntityCommand(workspace, entity, replacements)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        self.pick_point = point

        if self.boundary is None:
            return

        entity = self._hit(workspace, point, self.boundary)

        if entity is None or entity is self.boundary:
            self.target = None
            self.preview = []
            return

        self.target = entity
        self.preview = preview_extend(entity, self.boundary, point) or []

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

        self.boundary = None
        self.target = None
        self.preview = []
        self.pick_point = None
        self.status_text = "Extend: Select boundary edge"

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
            return self._rectangle_distance(entity, point)

        return None

    # --------------------------------

    def _rectangle_distance(self, entity, point):

        corners = self._rectangle_corners(entity)
        return min(
            self._segment_distance(point, start, end)
            for start, end in zip(corners, corners[1:] + corners[:1])
        )

    # --------------------------------

    def _rectangle_corners(self, entity):

        from engine.geometry import Vector2

        x1 = entity.p1.x
        y1 = entity.p1.y
        x2 = entity.p2.x
        y2 = entity.p2.y

        return [
            Vector2(x1, y1),
            Vector2(x2, y1),
            Vector2(x2, y2),
            Vector2(x1, y2),
        ]

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
