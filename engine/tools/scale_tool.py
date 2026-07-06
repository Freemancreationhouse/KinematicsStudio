from engine.commands import ScaleEntityCommand
from engine.geometry.primitives import point_to_segment_distance, rectangle_corners
from engine.geometry.scale import preview_scale, scale_entities
from engine.geometry.transforms import scale_factor_from_points
from engine.tools.tool import Tool


class ScaleTool(Tool):
    """Scale selected geometry using the V2 workspace and command systems."""

    def __init__(self):

        super().__init__()

        self.entities = []
        self.base_point = None
        self.reference_point = None
        self.preview = []
        self.factor = 1.0
        self.factor_text = ""
        self.status_text = "Scale: Select entities"

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
            self.status_text = "Scale: Pick reference point"
            return

        if self.reference_point is None:
            self.reference_point = point
            self.status_text = "Scale: Move cursor, type factor, click to confirm"
            return

        replacements = self._scaled_replacements()

        if not replacements:
            self.status_text = "Scale: No scale available"
            return

        workspace.command_manager.execute(
            ScaleEntityCommand(workspace, replacements)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if (
            not self.entities or
            self.base_point is None or
            self.reference_point is None
        ):
            return

        if not self.factor_text:
            self.factor = scale_factor_from_points(
                self.base_point,
                self.reference_point,
                point
            )
            self.status_text = f"Scale: Factor {self.factor:.3f}"

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
            self.factor_text = self.factor_text[:-1]
            self._sync_factor()
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            self._sync_factor()
            self._refresh_preview()
            return

        character = self._key_character(key)

        if character is None:
            return

        self.factor_text += character
        self._sync_factor()
        self._refresh_preview()

    # --------------------------------

    def cancel(self):

        self.entities = []
        self.base_point = None
        self.reference_point = None
        self.preview = []
        self.factor = 1.0
        self.factor_text = ""
        self.status_text = "Scale: Select entities"

    # --------------------------------

    def _load_or_pick_entities(self, workspace, point, additive):

        selection = getattr(workspace, "selection", None)
        selected = list(selection.selected) if selection else []

        if selected and not additive:
            self.entities = selected
            self.base_point = point
            self.status_text = "Scale: Pick reference point"
            return

        hit = self._hit(workspace, point)

        if hit is not None:
            if selection:
                selection.select(hit, additive)

            if additive and selected:
                self.entities = list(selection.selected)
            elif selected and hit in selected:
                self.entities = selected
            else:
                self.entities = [hit]

            self.status_text = f"Scale: Selected {len(self.entities)}. Pick base point"
            return

        if selected:
            self.entities = selected
            self.status_text = f"Scale: Selected {len(self.entities)}. Pick base point"
            return

        self.status_text = "Scale: Select entities"

    # --------------------------------

    def _scaled_replacements(self):

        replacements = []

        for entity in self.entities:
            result = scale_entities(entity, self.base_point, self.factor)

            if result:
                replacements.append((entity, result))

        return replacements

    # --------------------------------

    def _preview_entities(self):

        preview = []

        for entity in self.entities:
            result = preview_scale(entity, self.base_point, self.factor)

            if result:
                preview.extend(result)

        return preview

    # --------------------------------

    def _sync_factor(self):

        try:
            self.factor = float(self.factor_text) if self.factor_text else 1.0
        except ValueError:
            self.factor = 1.0

        if self.factor_text:
            self.status_text = f"Scale: Factor {self.factor:g}"
        else:
            self.status_text = "Scale: Move cursor, type factor, click to confirm"

    # --------------------------------

    def _refresh_preview(self):

        if (
            self.entities and
            self.base_point is not None and
            self.reference_point is not None
        ):
            self.preview = self._preview_entities()

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
            return point_to_segment_distance(point, entity.start, entity.end)

        if hasattr(entity, "p1") and hasattr(entity, "p2"):
            return self._rectangle_distance(entity, point)

        if hasattr(entity, "center") and hasattr(entity, "radius"):
            return abs(entity.center.distance_to(point) - entity.radius)

        return None

    # --------------------------------

    def _rectangle_distance(self, entity, point):

        corners = rectangle_corners(entity)
        return min(
            point_to_segment_distance(point, start, end)
            for start, end in zip(corners, corners[1:] + corners[:1])
        )
