from PySide6.QtCore import Qt


class PointTool:

    def mouse_press(self, canvas, event):

        if event.button() == Qt.MouseButton.LeftButton:
            canvas.points.append(event.position().toPoint())
            canvas.update()

    def mouse_move(self, canvas, event):
        pass

    def draw(self, painter):
        pass