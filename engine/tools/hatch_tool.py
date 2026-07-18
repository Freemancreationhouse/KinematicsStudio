from engine.commands import AddEntityCommand
from engine.entities import HatchEntity
from engine.geometry.hatch import boundary_points_from_entity, is_closed_boundary
from engine.tools.tool import Tool


class HatchTool(Tool):
    """Create associative hatches from selected closed boundary entities."""

    status_text = "Tool: Hatch"

    def __init__(self):

        super().__init__()
        self.preview = None

    # --------------------------------

    def activate(self):

        self.preview = None

    # --------------------------------

    def deactivate(self):

        self.preview = None

    # --------------------------------

    def mouse_press(self, workspace, point):

        boundary = self._selected_boundary(workspace)

        if boundary is None:
            return

        hatch = self._make_hatch(workspace, boundary)
        workspace.command_manager.execute(AddEntityCommand(workspace.entities, hatch))
        self.preview = None

    # --------------------------------

    def mouse_move(self, workspace, point):

        boundary = self._selected_boundary(workspace)
        self.preview = self._make_hatch(workspace, boundary) if boundary else None

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def _selected_boundary(self, workspace):

        selection = getattr(workspace, "selection", None)
        selected = list(getattr(selection, "selected", []) or [])

        for entity in selected:
            if is_closed_boundary(entity):
                return entity

        return None

    # --------------------------------

    def _make_hatch(self, workspace, boundary):

        pattern = getattr(workspace, "current_pattern", None)
        pattern_name = pattern.name if pattern else "SOLID"
        scale = pattern.scale if pattern else 10.0
        angle = pattern.angle if pattern else 45.0

        hatch = HatchEntity(
            boundary_points_from_entity(boundary),
            [boundary],
            pattern_name,
            scale,
            angle,
        )
        hatch.pattern = pattern

        return hatch
