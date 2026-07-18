from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from engine.commands import (
    RotateEntity3DCommand,
    ScaleEntity3DCommand,
    TranslateEntity3DCommand,
)
from engine.geometry import Vector3
from engine.picking3d import PickingManager3D
from engine.render import CameraController3D


class Viewport3D(QWidget):
    """Interactive 3D viewport for reusable 3D camera and renderer validation."""

    def __init__(self, app):

        super().__init__()

        self.app = app
        self.controller = CameraController3D(app.camera3d)
        self.picking = PickingManager3D()
        self.status_bar = None
        self.property_panel = None
        self._drag_mode = None
        self._gizmo_axis = None
        self._last_position = None
        self._press_position = None

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("3D View: left-drag orbit, middle/right-drag pan, wheel zoom.")

    # --------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#16191d"))
        self.app.render3d(painter, self.width(), self.height())
        painter.end()

    # --------------------------------

    def resizeEvent(self, event):

        self.app.camera3d.resize(self.width(), self.height())
        super().resizeEvent(event)

    # --------------------------------

    def mousePressEvent(self, event):

        self.setFocus()
        self._last_position = event.position()
        self._press_position = event.position()

        if event.button() == Qt.LeftButton:
            axis = self._pick_gizmo_axis(
                self.app.camera3d.screen_ray(event.position().x(), event.position().y())
            )

            if axis is not None:
                self._drag_mode = "gizmo"
                self._gizmo_axis = axis
                self.setCursor(Qt.SizeAllCursor)
                event.accept()
                return

            self._drag_mode = "orbit"
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._drag_mode = "pan"
            self.setCursor(Qt.SizeAllCursor)
            event.accept()
            return

        event.ignore()

    # --------------------------------

    def mouseMoveEvent(self, event):

        if self._drag_mode is None or self._last_position is None:
            self._hover(event.position())
            self._show_status()
            self.update()
            return

        current = event.position()
        dx = current.x() - self._last_position.x()
        dy = current.y() - self._last_position.y()

        if self._drag_mode == "gizmo":
            self._show_status()
            self.update()
        elif self._drag_mode == "orbit":
            self.controller.orbit(dx, dy)
        elif self._drag_mode == "pan":
            self.controller.pan(dx, dy)

        self._last_position = current
        self._show_status()
        self.update()

    # --------------------------------

    def mouseReleaseEvent(self, event):

        click = self._is_click(event.position())
        additive = bool(event.modifiers() & Qt.ControlModifier)
        drag_mode = self._drag_mode
        gizmo_axis = self._gizmo_axis
        press_position = self._press_position
        self._drag_mode = None
        self._gizmo_axis = None
        self._last_position = None
        self._press_position = None
        self.setCursor(Qt.OpenHandCursor)

        if drag_mode == "gizmo" and event.button() == Qt.LeftButton:
            self._apply_gizmo_drag(press_position, event.position(), gizmo_axis)
        elif click and event.button() == Qt.LeftButton:
            self._pick(event.position(), additive)

        self._show_status()
        self.update()

    # --------------------------------

    def wheelEvent(self, event):

        self.controller.zoom(event.angleDelta().y())
        self._show_status()
        self.update()

    # --------------------------------

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_F:
            self.fit_view()
            return

        if event.key() == Qt.Key_H:
            self.home_view()
            return

        if event.key() == Qt.Key_R:
            if event.modifiers() & Qt.ControlModifier:
                self._set_gizmo_mode("rotate")
                return

            self.reset_view()
            return

        if event.key() == Qt.Key_T:
            self._set_gizmo_mode("translate")
            return

        if event.key() == Qt.Key_S:
            self._set_gizmo_mode("scale")
            return

        if event.key() in (Qt.Key_X, Qt.Key_Y, Qt.Key_Z):
            self._set_gizmo_axis(chr(event.key()))
            return

        if event.key() == Qt.Key_W:
            self._set_gizmo_coordinate_mode("world")
            return

        if event.key() == Qt.Key_L:
            self._set_gizmo_coordinate_mode("local")
            return

        if event.key() == Qt.Key_P:
            self._cycle_gizmo_pivot()
            return

        event.ignore()

    # --------------------------------

    def fit_view(self):
        """Fit the 3D view to the default foundation bounds."""

        self.controller.fit_view()
        self._show_status()
        self.update()

    # --------------------------------

    def home_view(self):
        """Restore the 3D home view."""

        self.controller.home_view()
        self._show_status()
        self.update()

    # --------------------------------

    def reset_view(self):
        """Reset the 3D camera."""

        self.controller.reset_view()
        self._show_status()
        self.update()

    # --------------------------------

    def _show_status(self):

        if self.status_bar is None:
            return

        state = self.app.camera3d.state
        gizmo = getattr(self.app.workspace, "transform_gizmo", None)
        snap = getattr(self.app.workspace, "snap_manager3d", None)
        coordinate_manager = getattr(self.app.workspace, "coordinate_system_manager", None)
        plane_manager = getattr(self.app.workspace, "construction_plane_manager", None)
        mode = f"  Gizmo: {gizmo.mode}" if gizmo is not None else ""
        snap_text = ""

        if snap is not None:
            active = snap.active_snap.mode if snap.active_snap else ("ON" if snap.enabled else "OFF")
            snap_text = f"  Snap3D: {active}"

        ucs_text = ""

        if coordinate_manager is not None:
            ucs_text = f"  UCS: {coordinate_manager.active.name}"

        plane_text = ""

        if plane_manager is not None:
            plane_text = f"  Plane: {plane_manager.active.name}"

        self.status_bar.tool.setText("Tool: 3D View")
        self.status_bar.selected.setText(
            f"3D Camera: yaw {state.yaw:.0f}  pitch {state.pitch:.0f}  distance {state.distance:.0f}{mode}{snap_text}{ucs_text}{plane_text}"
        )

    # --------------------------------

    def _pick(self, position, additive=False):

        ray = self.app.camera3d.screen_ray(position.x(), position.y())
        hit = self.picking.pick(self.app.workspace, ray)
        selection = self.app.workspace.selection

        if hit is None:
            if not additive:
                selection.clear()
        else:
            selection.select(hit.entity, additive)

        self._pick_gizmo_axis(ray)
        self._sync_property_panel()

    # --------------------------------

    def _hover(self, position):

        ray = self.app.camera3d.screen_ray(position.x(), position.y())
        self.picking.hover(self.app.workspace, ray)
        self._update_snap(ray)
        self._pick_gizmo_axis(ray)

    # --------------------------------

    def _sync_property_panel(self):

        if self.property_panel is not None:
            self.property_panel.show_selection(self.app.workspace.selection.selected)

    # --------------------------------

    def _is_click(self, position):

        if self._press_position is None:
            return False

        dx = position.x() - self._press_position.x()
        dy = position.y() - self._press_position.y()

        return (dx * dx + dy * dy) <= 9.0

    # --------------------------------

    def _set_gizmo_mode(self, mode):

        gizmo = getattr(self.app.workspace, "transform_gizmo", None)

        if gizmo is not None:
            gizmo.set_mode(mode)
            self._show_status()
            self.update()

    # --------------------------------

    def _set_gizmo_axis(self, axis):

        gizmo = getattr(self.app.workspace, "transform_gizmo", None)

        if gizmo is not None:
            gizmo.set_axis_constraint(axis)
            self._show_status()
            self.update()

    # --------------------------------

    def _update_snap(self, ray):

        snap_manager = getattr(self.app.workspace, "snap_manager3d", None)

        if snap_manager is not None:
            snap_manager.snap_ray(self.app.workspace, ray, self.app.camera3d)

    # --------------------------------

    def _set_gizmo_coordinate_mode(self, mode):

        gizmo = getattr(self.app.workspace, "transform_gizmo", None)

        if gizmo is not None:
            gizmo.set_coordinate_mode(mode)
            self._show_status()
            self.update()

    # --------------------------------

    def _cycle_gizmo_pivot(self):

        gizmo = getattr(self.app.workspace, "transform_gizmo", None)

        if gizmo is None:
            return

        modes = list(gizmo.PIVOT_MODES)
        index = modes.index(gizmo.pivot_mode) if gizmo.pivot_mode in modes else 0
        gizmo.set_pivot_mode(modes[(index + 1) % len(modes)])
        self._show_status()
        self.update()

    # --------------------------------

    def _apply_gizmo_drag(self, start, end, axis):

        if start is None or end is None:
            return

        selected = [
            entity for entity in self.app.workspace.selection.selected
            if getattr(entity, "is_3d", False)
        ]

        if not selected:
            return

        gizmo = self.app.workspace.transform_gizmo
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        amount = (dx - dy) * 0.5
        pivot = gizmo.pivot_for_selection(selected)

        if gizmo.mode == "translate":
            delta = self._axis_vector(axis, amount)
            command = TranslateEntity3DCommand(
                self.app.workspace,
                selected,
                delta,
                pivot=pivot,
                axis=axis,
            )
        elif gizmo.mode == "rotate":
            rotation = self._axis_vector(axis, amount)
            command = RotateEntity3DCommand(
                self.app.workspace,
                selected,
                rotation,
                pivot=pivot,
                axis=axis,
            )
        else:
            factor = max(0.01, 1.0 + amount / 100.0)
            scale = self._axis_scale(axis, factor)
            command = ScaleEntity3DCommand(
                self.app.workspace,
                selected,
                scale,
                pivot=pivot,
                axis=axis,
            )

        self.app.workspace.command_manager.execute(command)
        self._sync_property_panel()

    # --------------------------------

    def _axis_vector(self, axis, value):

        if axis == "X":
            return Vector3(value, 0.0, 0.0)
        if axis == "Y":
            return Vector3(0.0, value, 0.0)
        if axis == "Z":
            return Vector3(0.0, 0.0, value)

        return Vector3(value, value, value)

    # --------------------------------

    def _axis_scale(self, axis, value):

        if axis == "X":
            return Vector3(value, 1.0, 1.0)
        if axis == "Y":
            return Vector3(1.0, value, 1.0)
        if axis == "Z":
            return Vector3(1.0, 1.0, value)

        return Vector3(value, value, value)

    # --------------------------------

    def _pick_gizmo_axis(self, ray):

        gizmo = getattr(self.app.workspace, "transform_gizmo", None)

        if gizmo is None:
            return None

        selected = [
            entity for entity in self.app.workspace.selection.selected
            if getattr(entity, "is_3d", False)
        ]

        if not selected:
            gizmo.highlighted_axis = None
            return None

        origin = gizmo.origin_for_selection(selected)

        return gizmo.pick_axis(ray, origin)
