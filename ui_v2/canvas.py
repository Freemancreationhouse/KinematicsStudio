from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from engine.cad import CADApplication
from engine.geometry import Vector2, BoundingBox


class Canvas(QWidget):

    def __init__(self):

        super().__init__()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)

        self.app = CADApplication()

        self.camera = self.app.camera
        self.property_panel = None
        self.status_bar = None
        self.panning = False
        self.pan_last = None
        self.snap_result = None

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

        if event.button() == Qt.MiddleButton:
            self.setFocus()
            self.panning = True
            self.pan_last = event.position()
            event.accept()
            return

        if event.button() != Qt.LeftButton:
            event.ignore()
            return

        self.setFocus()

        self.app.tool_manager.mouse_press(

            self.app.workspace,

            self._event_world(event, press=True),

            self._additive(event)

        )

        self._sync_selection_ui()
        self.update()

    # ------------------------------------------------

    def mouseMoveEvent(self, event):

        self._update_coordinates(event.position())

        if self.panning and self.pan_last is not None:
            current = event.position()
            dx = current.x() - self.pan_last.x()
            dy = current.y() - self.pan_last.y()
            self.camera.pan(-dx / self.camera.zoom, -dy / self.camera.zoom)
            self.pan_last = current
            self._sync_selection_ui()
            self.update()
            return

        self.app.tool_manager.mouse_move(

            self.app.workspace,

            self._event_world(event)

        )

        self._sync_selection_ui()
        self.update()

    # ------------------------------------------------

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MiddleButton:
            self.panning = False
            self.pan_last = None
            event.accept()
            self.update()
            return

        if event.button() != Qt.LeftButton:
            event.ignore()
            return

        self.app.tool_manager.mouse_release(

            self.app.workspace,

            self._event_world(event),

            self._additive(event)

        )

        self._sync_selection_ui()
        self.update()

    # ------------------------------------------------

    def keyPressEvent(self, event):

        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                self.app.workspace.command_manager.undo()
                self._sync_selection_ui()
                self.update()
                return

            if event.key() == Qt.Key_Y:
                self.app.workspace.command_manager.redo()
                self._sync_selection_ui()
                self.update()
                return

        if event.key() == Qt.Key_F3:
            self.app.snap_manager.toggle()
            self.snap_result = None
            self._sync_snap_ui()
            self.update()
            return

        self.app.tool_manager.key_press(
            self.app.workspace,
            event.key()
        )

        self._sync_selection_ui()
        self.update()

    # ------------------------------------------------

    def wheelEvent(self, event):

        factor = 1.05 if event.modifiers() & Qt.ControlModifier else 1.15

        if event.angleDelta().y() > 0:

            self.camera.zoom_at(
                Vector2(event.position().x(), event.position().y()),
                factor
            )

        else:

            self.camera.zoom_at(
                Vector2(event.position().x(), event.position().y()),
                1.0 / factor
            )

        self._update_coordinates(event.position())
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

            self.height(),

            self.snap_result

        )

        painter.end()

    # ------------------------------------------------

    def _additive(self, event):

        return bool(event.modifiers() & Qt.ControlModifier)

    # ------------------------------------------------

    def _sync_selection_ui(self):

        selection = getattr(self.app.workspace, "selection", None)

        if selection:
            for entity in list(selection.selected):
                if entity not in self.app.workspace.entities:
                    selection.deselect(entity)

        selected = selection.selected if selection else []

        if self.property_panel:
            self.property_panel.show_selection(selected)

        if self.status_bar:
            current = self.app.tool_manager.current

            if current and current.name == "MoveTool":
                self.status_bar.show_selection_count(selected)
            else:
                self.status_bar.show_selection(selected)

    # ------------------------------------------------

    def _update_coordinates(self, pos):

        if self.status_bar:
            world = self._world(pos)
            self.status_bar.show_coordinates(world, self.camera)
            self._sync_snap_ui()

    # ------------------------------------------------

    def _event_world(self, event, press=False):

        raw = self._world(event.position())

        if not self._tool_uses_snap(press):
            self.snap_result = None
            self._sync_snap_ui()
            return raw

        self.snap_result = self.app.snap_manager.snap(
            raw,
            self.app.workspace,
            self.camera
        )
        self._sync_snap_ui()

        if self.snap_result.mode == "OFF":
            return raw

        return self.snap_result.point

    # ------------------------------------------------

    def _tool_uses_snap(self, press=False):

        tool = self.app.tool_manager.current

        if tool is None:
            return False

        if tool.name == "SelectTool":
            return False

        if tool.name == "MoveTool" and press:
            return False

        return True

    # ------------------------------------------------

    def _sync_snap_ui(self):

        if not self.status_bar:
            return

        manager = self.app.snap_manager

        if not manager.enabled:
            self.status_bar.show_snap("OFF")
            self.setToolTip("Snap: OFF")
            return

        result = self.snap_result or manager.current
        mode = result.mode if result else "OFF"

        self.status_bar.show_snap(mode)
        self.setToolTip(f"Snap: {mode}")

    # ------------------------------------------------

    def fit_view(self):

        self.camera.fit_to_bounds(
            self._workspace_bounds(),
            self.width(),
            self.height()
        )
        self.update()

    # ------------------------------------------------

    def zoom_extents(self):

        self.fit_view()

    # ------------------------------------------------

    def _workspace_bounds(self):

        entities = [
            entity for entity in self.app.workspace.entities
            if getattr(entity, "visible", True)
        ]

        if not entities:
            return None

        bounds = BoundingBox()

        for entity in entities:
            box = entity.bounding_box
            bounds.add(box.min)
            bounds.add(box.max)

        return bounds
