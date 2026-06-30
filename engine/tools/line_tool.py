from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor


class LineTool:

    def __init__(self):
        self.lines = []
        self.current_start = None
        self.preview_end = None

    def mouse_press(self, canvas, event):

        point = event.position().toPoint()

        # LEFT CLICK
        if event.button() == Qt.MouseButton.LeftButton:

            if self.current_start is None:
                self.current_start = point
            else:
                self.lines.append((self.current_start, point))
                self.current_start = point

            self.preview_end = point
            canvas.update()

        # RIGHT CLICK = Finish
        elif event.button() == Qt.MouseButton.RightButton:

            self.current_start = None
            self.preview_end = None
            canvas.update()

    def mouse_move(self, canvas, event):

        if self.current_start is not None:
            self.preview_end = event.position().toPoint()
            canvas.update()

    def draw(self, painter):

        # Permanent lines
        painter.setPen(QPen(QColor("#00FFFF"), 2))

        for start, end in self.lines:
            painter.drawLine(start, end)

        # Preview line
        if self.current_start is not None and self.preview_end is not None:
            painter.drawLine(self.current_start, self.preview_end)