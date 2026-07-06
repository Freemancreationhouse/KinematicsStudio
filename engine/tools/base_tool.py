# DEPRECATED: Legacy canvas-event tool base retained for backward compatibility.
# V2 tools inherit from engine.tools.tool.Tool.

class BaseTool:

    def mouse_press(self, canvas, event):
        pass

    def mouse_move(self, canvas, event):
        pass

    def mouse_release(self, canvas, event):
        pass

    def key_press(self, canvas, event):
        pass

    def draw_preview(self, painter):
        pass
