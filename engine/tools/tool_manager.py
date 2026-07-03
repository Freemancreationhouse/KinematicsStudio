from .tool import Tool


class ToolManager:

    def __init__(self):

        self.tools = {}

        self.current = None

    # --------------------------------

    def register(self, tool: Tool):

        self.tools[tool.name] = tool

        if self.current is None:

            self.current = tool

    # --------------------------------

    def activate(self, name):

        if name not in self.tools:

            print("Tool not found:", name)
            return

        if self.current:

            self.current.deactivate()

        self.current = self.tools[name]

        self.current.activate()

        print("Active Tool ->", self.current.name)

    # --------------------------------

    def mouse_press(self, workspace, point):

        if self.current:

            self.current.mouse_press(workspace, point)

    # --------------------------------

    def mouse_move(self, workspace, point):

        if self.current:

            self.current.mouse_move(workspace, point)

    # --------------------------------

    def mouse_release(self, workspace, point):

        if self.current:

            self.current.mouse_release(workspace, point)

    # --------------------------------

    def key_press(self, workspace, key):

        if self.current:

            self.current.key_press(workspace, key)

    # --------------------------------

    def draw(self, painter):

        if self.current:

            self.current.draw_preview(painter)