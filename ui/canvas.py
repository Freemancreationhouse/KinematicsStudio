# DEPRECATED: Legacy canvas retained for backward compatibility.
# V2 uses ui_v2.canvas.Canvas.

from engine.tool_manager import ToolManager
from engine.project import Project

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPoint, QPointF


class Canvas(QWidget):

    def __init__(self):
        super().__init__()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        self.project = Project()
        self.tool_manager = ToolManager()

        self.zoom = 1.0
        self.pan = QPointF(0, 0)

        self.middle_pressed = False
        self.last_pan_pos = QPointF()

        self.mouse_pos = QPointF()

    def to_world(self, pos):

        return QPoint(
            int((pos.x() - self.pan.x()) / self.zoom),
            int((pos.y() - self.pan.y()) / self.zoom),
        )

    def wheelEvent(self, event):

        if event.angleDelta().y() > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1

        self.zoom = max(0.2, min(20.0, self.zoom))
        self.update()

    def mousePressEvent(self, event):

        self.setFocus()

        if event.button() == Qt.MiddleButton:
            self.middle_pressed = True
            self.last_pan_pos = event.position()
            return

        event.world_pos = self.to_world(event.position())

        self.tool_manager.mouse_press(self, event)

        self.update()

    def mouseMoveEvent(self, event):

        if self.middle_pressed:

            delta = event.position() - self.last_pan_pos

            self.pan += delta

            self.last_pan_pos = event.position()

            self.update()
            return

        self.mouse_pos = self.to_world(event.position())

        event.world_pos = self.mouse_pos

        self.tool_manager.mouse_move(self, event)

        self.update()

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MiddleButton:
            self.middle_pressed = False
            return

        self.tool_manager.mouse_release(self, event)

        self.update()

    def keyPressEvent(self, event):

        # Ctrl + Z
        if event.modifiers() & Qt.ControlModifier:

            if event.key() == Qt.Key_Z:
                self.project.undo()
                self.update()
                return

            if event.key() == Qt.Key_Y:
                self.project.redo()
                self.update()
                return

        self.tool_manager.key_press(self, event)

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor("#202020"))

        painter.translate(self.pan)

        painter.scale(self.zoom, self.zoom)

        # Grid
        painter.setPen(QColor("#404040"))

        grid = 25

        for x in range(-5000, 5000, grid):
            painter.drawLine(x, -5000, x, 5000)

        for y in range(-5000, 5000, grid):
            painter.drawLine(-5000, y, 5000, y)

        # Crosshair
        painter.setPen(QPen(QColor("#D4A017"), 1))

        painter.drawLine(
            self.mouse_pos.x(),
            -5000,
            self.mouse_pos.x(),
            5000,
        )

        painter.drawLine(
            -5000,
            self.mouse_pos.y(),
            5000,
            self.mouse_pos.y(),
        )

        # Draw entities
        for entity in self.project.entities:
            entity.draw(painter)

        # Draw active tool preview
        self.tool_manager.draw(painter)
