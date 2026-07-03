from engine.tools import Tool, ToolManager


class DummyTool(Tool):

    def mouse_press(self, workspace, point):
        print("press")

    def mouse_move(self, workspace, point):
        print("move")

    def mouse_release(self, workspace, point):
        print("release")


manager = ToolManager()

manager.register(DummyTool())

print(manager.current.name)

manager.mouse_press(None, None)