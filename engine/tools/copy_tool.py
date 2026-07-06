from engine.commands import CopyEntityCommand
from engine.geometry.copy import copy_entities, preview_copy
from engine.tools.entity_pick import hit_entity
from engine.tools.tool import Tool


class CopyTool(Tool):
    """Copy selected geometry using base and destination points."""

    def __init__(self):

        super().__init__()

        self.entities = []
        self.base_point = None
        self.preview = []
        self.status_text = "Copy: Select entities"

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
            self.status_text = "Copy: Pick destination point"
            return

        copied = self._copied_entities(point)

        if not copied:
            self.status_text = "Copy: No copy available"
            return

        workspace.command_manager.execute(
            CopyEntityCommand(workspace, copied)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        if not self.entities or self.base_point is None:
            return

        self.preview = self._preview_entities(point)
        self.status_text = f"Copy: Preview {len(self.preview)} entities"

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
        self.base_point = None
        self.preview = []
        self.status_text = "Copy: Select entities"

    # --------------------------------

    def _load_or_pick_entities(self, workspace, point, additive):

        selection = getattr(workspace, "selection", None)
        selected = list(selection.selected) if selection else []
        hit = hit_entity(workspace, point)

        if selected and hit is None:
            self.entities = selected
            self.base_point = point
            self.status_text = "Copy: Pick destination point"
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

            self.status_text = f"Copy: Selected {len(self.entities)}. Pick base point"
            return

        if selected:
            self.entities = selected
            self.status_text = f"Copy: Selected {len(self.entities)}. Pick base point"
            return

        self.status_text = "Copy: Select entities"

    # --------------------------------

    def _copied_entities(self, point):

        dx = point.x - self.base_point.x
        dy = point.y - self.base_point.y
        copied = []

        for entity in self.entities:
            copied.extend(copy_entities(entity, dx, dy))

        return copied

    # --------------------------------

    def _preview_entities(self, point):

        dx = point.x - self.base_point.x
        dy = point.y - self.base_point.y
        preview = []

        for entity in self.entities:
            preview.extend(preview_copy(entity, dx, dy))

        return preview
