from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from engine.cad import CADApplication
from engine.geometry import Vector2


class Canvas(QWidget):

    def __init__(self):

        super().__init__()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.app = CADApplication()

        self.camera = self.app.camera

    # ------------------------------------------------

    def _world(self, pos):

        p = self.camera.screen_to_world(

            Vector2(

                pos.x(),

                pos.y()

            )

        )

        return p

    # ------------------------------------------------

    def mousePressEvent(self, event):

        if event.button() != Qt.LeftButton:
            event.ignore()
            return

        self.setFocus()

        self.app.tool_manager.mouse_press(

            self.app.workspace,

            self._world(event.position())

        )

        self.update()

    # ------------------------------------------------

    def mouseMoveEvent(self, event):

        self.app.tool_manager.mouse_move(

            self.app.workspace,

            self._world(event.position())

        )

        self.update()

    # ------------------------------------------------

    def mouseReleaseEvent(self, event):

        if event.button() != Qt.LeftButton:
            event.ignore()
            return

        self.app.tool_manager.mouse_release(

            self.app.workspace,

            self._world(event.position())

        )

        self.update()

    # ------------------------------------------------

    def keyPressEvent(self, event):

        self.app.tool_manager.key_press(
            self.app.workspace,
            event.key()
        )

        self.update()

    # ------------------------------------------------

    def wheelEvent(self, event):

        if event.angleDelta().y() > 0:

            self.camera.zoom_in()

        else:

            self.camera.zoom_out()

        self.update()

    # ------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.fillRect(

            self.rect(),

            QColor("#202020")

        )

        self.app.render(

            painter,

            self.width(),

            self.height()

        )

        painter.end()
