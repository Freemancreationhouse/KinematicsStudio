from engine.commands import ExplodeBlockCommand
from engine.entities import BlockReference
from engine.tools.entity_pick import hit_entity
from engine.tools.tool import Tool


class ExplodeBlockTool(Tool):
    """Explode a selected or picked BlockReference through a command."""

    def __init__(self):

        super().__init__()
        self.status_text = "Explode Block: Select block reference"

    # --------------------------------

    def activate(self):

        self.status_text = "Explode Block: Select block reference"

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        reference = self._selected_reference(workspace)

        if reference is None:
            hit = hit_entity(workspace, point)
            reference = hit if isinstance(hit, BlockReference) else None

        if reference is None:
            self.status_text = "Explode Block: No block reference selected"
            return

        workspace.command_manager.execute(
            ExplodeBlockCommand(workspace, reference)
        )
        self.status_text = "Explode Block: Complete"

    # --------------------------------

    def mouse_move(self, workspace, point):

        pass

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):

        pass

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.status_text = "Explode Block: Cancelled"

    # --------------------------------

    def _selected_reference(self, workspace):

        selection = getattr(workspace, "selection", None)

        if not selection:
            return None

        for entity in selection.selected:
            if isinstance(entity, BlockReference):
                return entity

        return None
