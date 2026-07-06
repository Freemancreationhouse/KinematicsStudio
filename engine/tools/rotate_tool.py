from math import atan2, degrees

from engine.commands import RotateEntityCommand
from engine.geometry.rotate import preview_rotate, rotate_entities
from engine.tools.tool import Tool


class RotateTool(Tool):
    """Rotate selected geometry using the V2 workspace and command systems."""

    def __init__(self):

        super().__init__()

        self.entities = []
        self.base_point = None
        self.preview = []
        self.angle = 0.0
        self.angle_text = ""
        self.status_text = "Rotate: Select entities"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        if workspace is None:
            return

        if not self.entities:
            self._load_or_pick_entities(workspace, point, additive)
            return

        if self.base_point is None:
            self.base_point = point
            self.status_text = "Rotate: Move cursor, type angle, click to confirm"
            return

        replacements = self._rotated_replacements()

        if not replacements:
            self.status_text = "Rotate: No rotation available"
            return

        workspace.command_manager.execute(
            RotateEntityCommand(workspace, replacements)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.entities or self.base_point is None:
            return

        if not self.angle_text:
            self.angle = self._mouse_angle(point)
            self.status_text = f"Rotate: Angle {self.angle:.1f}"

        self.preview = self._preview_entities()

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):

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
            self.angle_text = self.angle_text[:-1]
            self._sync_angle()
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            self._sync_angle()
            self.preview = self._preview_entities()
            return

        character = self._key_character(key)

        if character is None:
            return

        self.angle_text += character
        self._sync_angle()
        self.preview = self._preview_entities()

    # --------------------------------

    def cancel(self):

        self.entities = []
        self.base_point = None
        self.preview = []
        self.angle = 0.0
        self.angle_text = ""
        self.status_text = "Rotate: Select entities"

    # --------------------------------

    def _load_or_pick_entities(self, workspace, point, additive):

        selection = getattr(workspace, "selection", None)
        selected = list(selection.selected) if selection else []
        hit = self._hit(workspace, point)

        if selected and hit is None:
            self.entities = selected
            self.base_point = point
            self.status_text = "Rotate: Move cursor, type angle, click to confirm"
            return

        if hit is not None:
            if selection:
                selection.select(hit, additive)

            if additive and selected:
                self.entities = list(selection.selected)
            elif selected and hit in selected:
                self.entities = selected
            else:
                self.entities = [hit]

            self.status_text = f"Rotate: Selected {len(self.entities)}. Select base point"
            return

        if selected:
            self.entities = selected
            self.status_text = f"Rotate: Selected {len(self.entities)}. Select base point"
            return

        self.status_text = "Rotate: Select entities"

    # --------------------------------

    def _rotated_replacements(self):

        replacements = []

        for entity in self.entities:
            result = rotate_entities(entity, self.base_point, self.angle)

            if result:
                replacements.append((entity, result))

        return replacements

    # --------------------------------

    def _preview_entities(self):

        preview = []

        for entity in self.entities:
            result = preview_rotate(entity, self.base_point, self.angle)

            if result:
                preview.extend(result)

        return preview

    # --------------------------------

    def _mouse_angle(self, point):

        dx = point.x - self.base_point.x
        dy = point.y - self.base_point.y

        if dx == 0 and dy == 0:
            return 0.0

        return degrees(atan2(dy, dx))

    # --------------------------------

    def _sync_angle(self):

        try:
            self.angle = float(self.angle_text) if self.angle_text else 0.0
        except ValueError:
            self.angle = 0.0

        if self.angle_text:
            self.status_text = f"Rotate: Angle {self.angle:g}"
        else:
            self.status_text = "Rotate: Move cursor, type angle, click to confirm"

    # --------------------------------

    def _key_character(self, key):

        key_text = str(key)

        if len(key_text) == 1 and (
            key_text.isdigit() or key_text in ".-"
        ):
            return key_text

        if isinstance(key, int):
            if 48 <= key <= 57:
                return chr(key)

            if key == 46:
                return "."

            if key == 45:
                return "-"

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

        if hasattr(entity, "center") and hasattr(entity, "radius"):
            return abs(entity.center.distance_to(point) - entity.radius)

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
