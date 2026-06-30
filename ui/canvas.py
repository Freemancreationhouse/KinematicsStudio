from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPoint


class Canvas(QWidget):

    def __init__(self):
        super().__init__()

        self.setMouseTracking(True)

        self.mouse_pos = QPoint(0, 0)

        self.points = []

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.position().toPoint()
        self.update()


    def mousePressEvent(self, event):

     if event.button() == Qt.MouseButton.LeftButton:
        self.points.append(event.position().toPoint())
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor("#202020"))

        painter.setPen(QColor("#404040"))

        grid = 25

        for x in range(0, self.width(), grid):
            painter.drawLine(x, 0, x, self.height())

        for y in range(0, self.height(), grid):
            painter.drawLine(0, y, self.width(), y)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#D4A017"))

        for point in self.points:
            painter.drawEllipse(point, 4, 4)

        # Draw mouse crosshair
        painter.setPen(QPen(QColor("#D4A017"), 1))

        x = self.mouse_pos.x()
        y = self.mouse_pos.y()

        painter.drawLine(x, 0, x, self.height())
        painter.drawLine(0, y, self.width(), y)
        
       # Draw clicked points
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#D4A017"))

        for point in self.points:
         painter.drawEllipse(point, 4, 4)