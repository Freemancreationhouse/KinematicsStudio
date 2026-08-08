from .tool import Tool


class ToolManager:

    SELECT_TOOL_NAME = "SelectTool"
    ESCAPE_KEYS = {"Escape", "Esc", 0x01000000}
    ENTER_KEYS = {"Enter", "Return", 0x01000004, 0x01000005}
    MULTI_SEGMENT_TOOLS = {
        "PolylineTool",
        "ClosedPolylineTool",
        "SplineTool",
    }

    def __init__(self):

        self.tools = {}

        self.current = None
        self.on_change = None

    # --------------------------------

    def register(self, tool: Tool):

        self.tools[tool.name] = tool

        if self.current is None:

            self.current = tool
            self.current.activate()

        return tool

    # --------------------------------

    def activate(self, name):

        if name not in self.tools:

            return False

        if self.current:

            self.current.deactivate()

        self.current = self.tools[name]

        self.current.activate()

        if self.on_change:
            self.on_change(self.current)

        return True

    # --------------------------------

    def activate_select(self):
        """Cancel the current tool and restore the default Select tool."""

        return self.activate(self.SELECT_TOOL_NAME)

    # --------------------------------

    def cancel_active(self):
        """Cancel transient state for the current active tool."""

        if self.current:
            self.current.deactivate()

    # --------------------------------

    @property
    def active_tool(self):
        """Return the single active tool."""

        return self.current

    # --------------------------------

    @property
    def current_tool(self):
        """Compatibility alias for the single active tool."""

        return self.current

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):

        if self.current:

            tool = self.current

            try:
                tool.mouse_press(workspace, point, additive)
            except TypeError:
                tool.mouse_press(workspace, point)

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.current:

            self.current.mouse_move(workspace, point)

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):

        if self.current:

            tool = self.current

            try:
                tool.mouse_release(workspace, point, additive)
            except TypeError:
                tool.mouse_release(workspace, point)

    # --------------------------------

    def key_press(self, workspace, key):

        if key in self.ESCAPE_KEYS:
            self.cancel_active()
            self.activate_select()
            return

        if self.current:

            tool = self.current
            tool.key_press(workspace, key)

            if key in self.ENTER_KEYS and tool.name in self.MULTI_SEGMENT_TOOLS:
                self.activate_select()
                return

    # --------------------------------

    def draw(self, painter):

        if self.current:

            self.current.draw_preview(painter)

    # --------------------------------

    def _command_count(self, workspace):
        """Return the active workspace command count for lifecycle detection."""

        command_manager = getattr(workspace, "command_manager", None)
        if command_manager is None:
            return 0

        undo_count = getattr(command_manager, "undo_count", None)
        if undo_count is not None:
            return undo_count

        undo_stack = getattr(command_manager, "undo_stack", None)
        if undo_stack is not None:
            return len(undo_stack)

        return 0
