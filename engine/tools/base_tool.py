from PySide6.QtCore import Qt


class BaseTool:
    """Base class for all drawing tools."""

    def mouse_press(self, canvas, event):
        pass

    def mouse_move(self, canvas, event):
        pass

    def mouse_release(self, canvas, event):
        pass

    def draw(self, painter):
        pass