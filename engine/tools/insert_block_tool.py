from engine.commands import InsertBlockCommand
from engine.entities import BlockReference
from engine.tools.tool import Tool


class InsertBlockTool(Tool):
    """Insert the current block definition with live preview."""

    def __init__(self):

        super().__init__()
        self.definition = None
        self.preview = None
        self.status_text = "Insert Block: Choose block"

    # --------------------------------

    def activate(self):

        self.definition = None
        self.preview = None
        self.status_text = "Insert Block: Choose block"

    # --------------------------------

    def deactivate(self):

        self.cancel()

    # --------------------------------

    def mouse_press(self, workspace, point):

        self._load_definition(workspace)

        if self.definition is None:
            self.status_text = "Insert Block: No block definition"
            return

        workspace.command_manager.execute(
            InsertBlockCommand(workspace, self.definition, point)
        )
        self.cancel()

    # --------------------------------

    def mouse_move(self, workspace, point):

        self._load_definition(workspace)

        if self.definition is None:
            return

        self.preview = BlockReference(self.definition, point.copy())
        self.status_text = f"Insert Block: {self.definition.name}"

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        if self.preview:
            previous = self.preview.selected
            self.preview.selected = True
            self.preview.draw(painter)
            self.preview.selected = previous

    # --------------------------------

    def key_press(self, workspace, key):

        if key in ("Escape", "Esc", 0x01000000):
            self.cancel()

    # --------------------------------

    def cancel(self):

        self.preview = None
        self.status_text = "Insert Block: Choose block"

    # --------------------------------

    def _load_definition(self, workspace):

        if workspace is None:
            return

        manager = workspace.block_manager

        self.definition = manager.current

        if self.definition is None and manager.definitions:
            self.definition = manager.definitions[0]
            manager.set_current(self.definition)
