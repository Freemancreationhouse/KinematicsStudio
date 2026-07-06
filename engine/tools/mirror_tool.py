from engine.commands import MirrorEntityCommand
from engine.geometry.mirror import mirror_entities, preview_mirror
from engine.tools.tool import Tool


class MirrorTool(Tool):
    """Mirror selected geometry using the V2 workspace and command systems."""

    def __init__(self):

        super().__init__()

        self.entities = []
        self.line_start = None
        self.line_end = None
        self.preview = []
        self.status_text = "Mirror: Select entities"

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

        if self.line_start is None:
            self.line_start = point
            self.status_text = "Mirror: Select second mirror-line point"
            return

        self.line_end = point
        replacements = self._mirrored_replacements()

        if not replacements:
            self.status_text = "Mirror: No mirror available"
            self.preview = []
            return

        workspace.command_manager.execute(
            MirrorEntityCommand(workspace, replacements)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.entities or self.line_start is None:
            return

        self.line_end = point
        self.preview = self._preview_entities()
        self.status_text = "Mirror: Preview. Click to confirm"

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

    # --------------------------------

    def cancel(self):

        self.entities = []
        self.line_start = None
        self.line_end = None
        self.preview = []
        self.status_text = "Mirror: Select entities"

    # --------------------------------

    def _load_or_pick_entities(self, workspace, point, additive):

        selection = getattr(workspace, "selection", None)
        selected = list(selection.selected) if selection else []
        hit = self._hit(workspace, point)

        if selected and hit is None:
            self.entities = selected
            self.line_start = point
            self.status_text = "Mirror: Select second mirror-line point"
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

            self.status_text = f"Mirror: Selected {len(self.entities)}. Select first mirror-line point"
            return

        if selected:
            self.entities = selected
            self.status_text = f"Mirror: Selected {len(self.entities)}. Select first mirror-line point"
            return

        self.status_text = "Mirror: Select entities"

    # --------------------------------

    def _mirrored_replacements(self):

        replacements = []

        for entity in self.entities:
            result = mirror_entities(entity, self.line_start, self.line_end)

            if result:
                replacements.append((entity, result))

        return replacements

    # --------------------------------

    def _preview_entities(self):

        preview = []

        for entity in self.entities:
            result = preview_mirror(entity, self.line_start, self.line_end)

            if result:
                preview.extend(result)

        return preview

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
