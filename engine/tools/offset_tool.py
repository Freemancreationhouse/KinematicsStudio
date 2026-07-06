from engine.commands import OffsetEntityCommand
from engine.geometry.offset import offset_entities, preview_offset
from engine.tools.tool import Tool


class OffsetTool(Tool):
    """Offset selected geometry using the V2 workspace and command systems."""

    def __init__(self):

        super().__init__()

        self.source = None
        self.preview = []
        self.pick_point = None
        self.distance = None
        self.distance_text = ""
        self.status_text = "Offset: Select entity"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point):

        if self.source is None:
            self.source = self._hit(workspace, point)

            if self.source is not None:
                self.status_text = "Offset: Move cursor, type distance, click to confirm"

            return

        offsets = offset_entities(self.source, point, self.distance)

        if not offsets:
            self.status_text = "Offset: No offset available"
            self.preview = []
            return

        workspace.command_manager.execute(
            OffsetEntityCommand(workspace, self.source, offsets)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        self.pick_point = point

        if self.source is None:
            return

        self.preview = preview_offset(self.source, point, self.distance) or []

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
            return

        if key in ("Backspace", 0x01000003):
            self.distance_text = self.distance_text[:-1]
            self._sync_distance()
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            self._sync_distance()
            return

        character = self._key_character(key)

        if character is None:
            return

        self.distance_text += character
        self._sync_distance()

    # --------------------------------

    def cancel(self):

        self.source = None
        self.preview = []
        self.pick_point = None
        self.distance = None
        self.distance_text = ""
        self.status_text = "Offset: Select entity"

    # --------------------------------

    def _sync_distance(self):

        try:
            self.distance = float(self.distance_text) if self.distance_text else None
        except ValueError:
            self.distance = None

        if self.distance is None:
            self.status_text = "Offset: Move cursor, type distance, click to confirm"
        else:
            self.status_text = f"Offset: Distance {self.distance:g}"

    # --------------------------------

    def _key_character(self, key):

        key_text = str(key)

        if len(key_text) == 1 and (key_text.isdigit() or key_text == "."):
            return key_text

        if isinstance(key, int):
            if 48 <= key <= 57:
                return chr(key)

            if key == 46:
                return "."

        return None

    # --------------------------------

    def _hit(self, workspace, point):

        candidates = (
            workspace.selectable_entities()
            if hasattr(workspace, "selectable_entities")
            else workspace.entities
        )

        best = None
        best_distance = 8.0

        for entity in reversed(candidates):
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
