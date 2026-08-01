from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QEasingCurve, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from engine.geometry import Vector3
from engine.render.camera3d import Camera3D, Camera3DState


@dataclass(frozen=True)
class ViewCubeOrientation:
    """Camera orientation target represented by orbit angles and projection."""

    name: str
    yaw: float
    pitch: float
    projection_mode: str


@dataclass(frozen=True)
class ViewCubeRegion:
    """Interactive ViewCube region used for hit testing and painting."""

    key: str
    label: str
    rect: QRectF
    orientation: ViewCubeOrientation
    kind: str


class ViewCube(QWidget):
    """Professional CAD ViewCube overlay for independent 3D viewport cameras."""

    orientationChanged = Signal(str)

    _DURATION_MS = 260

    def __init__(
        self,
        camera: Camera3D,
        parent: QWidget | None = None,
    ) -> None:
        """Create a ViewCube bound to a single independent camera."""

        super().__init__(parent)

        self._camera = camera
        self._hover_key: str | None = None
        self._regions: list[ViewCubeRegion] = []
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(16)
        self._animation_timer.timeout.connect(self._advance_animation)
        self._animation_step = 0
        self._animation_steps = max(1, self._DURATION_MS // 16)
        self._start_state: Camera3DState | None = None
        self._target_state: Camera3DState | None = None
        self._target_name = ""
        self._easing = QEasingCurve(QEasingCurve.Type.InOutCubic)

        self.setObjectName("KinematicsViewCube")
        self.setFixedSize(148, 172)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        if parent is not None:
            parent.installEventFilter(self)
        self.reposition()
        self.show()

    def reposition(self) -> None:
        """Place the ViewCube in the upper-right corner of its viewport."""

        parent = self.parentWidget()
        if parent is None:
            return

        margin = 16
        self.move(
            max(margin, parent.width() - self.width() - margin),
            margin,
        )
        self.raise_()

    def paintEvent(self, event) -> None:
        """Paint the cube, compass and home control."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._build_regions()
        self._draw_panel(painter)
        self._draw_home_button(painter)
        self._draw_compass(painter)
        self._draw_cube(painter)
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        """Highlight the cube region under the cursor."""

        key = self._region_at(event.position())
        if key != self._hover_key:
            self._hover_key = key
            self.update()
        event.accept()

    def leaveEvent(self, event) -> None:
        """Clear hover feedback when the pointer exits the ViewCube."""

        self._hover_key = None
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle ViewCube orientation and home clicks."""

        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return

        key = self._region_at(event.position())
        if key == "home":
            self.home()
            event.accept()
            return

        region = self._region_by_key(key)
        if region is not None:
            self.orient_to(region.orientation)
            event.accept()
            return

        event.ignore()

    def eventFilter(self, watched, event) -> bool:
        """Keep the overlay pinned while the parent viewport resizes."""

        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.reposition()
        return super().eventFilter(watched, event)

    def home(self) -> None:
        """Animate to the camera's default home state."""

        default_state = getattr(self._camera, "_default_state", None)
        if default_state is None:
            default_state = Camera3DState()
        self._animate_to_state(default_state, "Home")

    def orient_to(self, orientation: ViewCubeOrientation) -> None:
        """Animate to a named ViewCube orientation."""

        target = Camera3DState.from_dict(self._camera.state.to_dict())
        target.yaw = orientation.yaw
        target.pitch = orientation.pitch
        target.projection_mode = orientation.projection_mode
        self._animate_to_state(target, orientation.name)

    def _animate_to_state(self, target: Camera3DState, name: str) -> None:
        """Start a smooth camera transition without replacing the camera."""

        self._start_state = Camera3DState.from_dict(self._camera.state.to_dict())
        self._target_state = Camera3DState.from_dict(target.to_dict())
        self._target_name = name
        self._animation_step = 0

        if self._camera.state.projection_mode != target.projection_mode:
            self._camera.state.projection_mode = target.projection_mode

        if not self._animation_timer.isActive():
            self._animation_timer.start()

    def _advance_animation(self) -> None:
        """Advance the active animated camera transition."""

        if self._start_state is None or self._target_state is None:
            self._animation_timer.stop()
            return

        self._animation_step += 1
        raw_t = min(1.0, self._animation_step / self._animation_steps)
        t = float(self._easing.valueForProgress(raw_t))
        state = self._camera.state
        state.yaw = self._angle_lerp(
            self._start_state.yaw,
            self._target_state.yaw,
            t,
        )
        state.pitch = self._lerp(self._start_state.pitch, self._target_state.pitch, t)
        state.distance = self._lerp(
            self._start_state.distance,
            self._target_state.distance,
            t,
        )
        state.orthographic_scale = self._lerp(
            self._start_state.orthographic_scale,
            self._target_state.orthographic_scale,
            t,
        )
        state.target = Vector3(
            self._lerp(self._start_state.target.x, self._target_state.target.x, t),
            self._lerp(self._start_state.target.y, self._target_state.target.y, t),
            self._lerp(self._start_state.target.z, self._target_state.target.z, t),
        )

        parent = self.parentWidget()
        if parent is not None:
            parent.update()
        self.update()

        if raw_t >= 1.0:
            state.projection_mode = self._target_state.projection_mode
            self._animation_timer.stop()
            self.orientationChanged.emit(self._target_name)

    def _build_regions(self) -> None:
        """Build current clickable face, edge and corner regions."""

        cube = QRectF(31.0, 58.0, 86.0, 86.0)
        small = 18.0
        medium = 24.0
        self._regions = [
            ViewCubeRegion(
                "corner_nw",
                "",
                QRectF(cube.left(), cube.top(), small, small),
                ViewCubeOrientation("Top Left Front", 135.0, 35.0, "perspective"),
                "corner",
            ),
            ViewCubeRegion(
                "corner_ne",
                "",
                QRectF(cube.right() - small, cube.top(), small, small),
                ViewCubeOrientation("Top Right Front", 45.0, 35.0, "perspective"),
                "corner",
            ),
            ViewCubeRegion(
                "corner_sw",
                "",
                QRectF(cube.left(), cube.bottom() - small, small, small),
                ViewCubeOrientation("Bottom Left Front", 225.0, -30.0, "perspective"),
                "corner",
            ),
            ViewCubeRegion(
                "corner_se",
                "",
                QRectF(cube.right() - small, cube.bottom() - small, small, small),
                ViewCubeOrientation("Bottom Right Front", 315.0, -30.0, "perspective"),
                "corner",
            ),
            ViewCubeRegion(
                "edge_top",
                "",
                QRectF(
                    cube.left() + small,
                    cube.top(),
                    cube.width() - 2 * small,
                    small,
                ),
                ViewCubeOrientation("Top Front", 90.0, 35.0, "perspective"),
                "edge",
            ),
            ViewCubeRegion(
                "edge_bottom",
                "",
                QRectF(
                    cube.left() + small,
                    cube.bottom() - small,
                    cube.width() - 2 * small,
                    small,
                ),
                ViewCubeOrientation("Bottom Front", 270.0, -30.0, "perspective"),
                "edge",
            ),
            ViewCubeRegion(
                "edge_left",
                "",
                QRectF(
                    cube.left(),
                    cube.top() + small,
                    small,
                    cube.height() - 2 * small,
                ),
                ViewCubeOrientation("Left Front", 180.0, 20.0, "perspective"),
                "edge",
            ),
            ViewCubeRegion(
                "edge_right",
                "",
                QRectF(
                    cube.right() - small,
                    cube.top() + small,
                    small,
                    cube.height() - 2 * small,
                ),
                ViewCubeOrientation("Right Front", 0.0, 20.0, "perspective"),
                "edge",
            ),
            ViewCubeRegion(
                "top",
                "TOP",
                QRectF(
                    cube.left() + medium,
                    cube.top(),
                    cube.width() - 2 * medium,
                    medium,
                ),
                ViewCubeOrientation("Top", -90.0, 89.0, "orthographic"),
                "face",
            ),
            ViewCubeRegion(
                "bottom",
                "BOTTOM",
                QRectF(
                    cube.left() + medium,
                    cube.bottom() - medium,
                    cube.width() - 2 * medium,
                    medium,
                ),
                ViewCubeOrientation("Bottom", -90.0, -89.0, "orthographic"),
                "face",
            ),
            ViewCubeRegion(
                "left",
                "LEFT",
                QRectF(
                    cube.left(),
                    cube.top() + medium,
                    medium,
                    cube.height() - 2 * medium,
                ),
                ViewCubeOrientation("Left", 0.0, 0.0, "orthographic"),
                "face",
            ),
            ViewCubeRegion(
                "right",
                "RIGHT",
                QRectF(
                    cube.right() - medium,
                    cube.top() + medium,
                    medium,
                    cube.height() - 2 * medium,
                ),
                ViewCubeOrientation("Right", 180.0, 0.0, "orthographic"),
                "face",
            ),
            ViewCubeRegion(
                "front",
                "FRONT",
                QRectF(
                    cube.left() + medium,
                    cube.top() + medium,
                    cube.width() - 2 * medium,
                    cube.height() - 2 * medium,
                ),
                ViewCubeOrientation("Front", -90.0, 0.0, "orthographic"),
                "face",
            ),
            ViewCubeRegion(
                "back",
                "BACK",
                QRectF(cube.left() + 23.0, cube.top() - 24.0, 40.0, 20.0),
                ViewCubeOrientation("Back", 90.0, 0.0, "orthographic"),
                "face",
            ),
        ]

    def _draw_panel(self, painter: QPainter) -> None:
        """Draw the translucent overlay surface."""

        painter.setPen(QPen(QColor(96, 106, 120, 120), 1))
        painter.setBrush(QColor(21, 24, 29, 186))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)

    def _draw_home_button(self, painter: QPainter) -> None:
        """Draw the ViewCube home control."""

        rect = self._home_rect()
        hovered = self._hover_key == "home"
        painter.setPen(QPen(QColor("#7F8A99"), 1))
        painter.setBrush(QColor("#2F3640") if hovered else QColor("#252B33"))
        painter.drawRoundedRect(rect, 5, 5)
        painter.setPen(QColor("#E4E9F0"))
        painter.setFont(self._font(8, True))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "HOME")

    def _draw_compass(self, painter: QPainter) -> None:
        """Draw a compact north compass that rotates with the camera yaw."""

        center = QPointF(116.0, 33.0)
        radius = 15.0
        yaw = math.radians(getattr(self._camera.state, "yaw", 0.0))
        direction = QPointF(math.sin(-yaw) * radius, -math.cos(-yaw) * radius)

        painter.setPen(QPen(QColor("#56616E"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)
        painter.setPen(QPen(QColor("#4FA3FF"), 2))
        painter.drawLine(center, center + direction)
        painter.setPen(QColor("#DCE5F2"))
        painter.setFont(self._font(8, True))
        painter.drawText(
            QRectF(center.x() - 9.0, center.y() - 31.0, 18.0, 12.0),
            Qt.AlignmentFlag.AlignCenter,
            "N",
        )

    def _draw_cube(self, painter: QPainter) -> None:
        """Draw cube faces, edge zones and corner zones."""

        cube_path = QPainterPath()
        cube_path.addRoundedRect(QRectF(31.0, 58.0, 86.0, 86.0), 7, 7)
        painter.setPen(QPen(QColor("#657182"), 1))
        painter.setBrush(QColor("#232A33"))
        painter.drawPath(cube_path)

        for region in self._regions:
            if region.key == "back":
                self._draw_region(painter, region)

        for region in self._regions:
            if region.kind in {"corner", "edge"} and region.key != "back":
                self._draw_region(painter, region)

        for region in self._regions:
            if region.kind == "face" and region.key != "back":
                self._draw_region(painter, region)

    def _draw_region(self, painter: QPainter, region: ViewCubeRegion) -> None:
        """Draw one interactive ViewCube region."""

        hovered = region.key == self._hover_key
        if region.kind == "face":
            base = QColor("#313A46")
            hover = QColor("#4FA3FF")
            alpha = 224 if hovered else 184
        elif region.kind == "edge":
            base = QColor("#27313B")
            hover = QColor("#74B7FF")
            alpha = 210 if hovered else 90
        else:
            base = QColor("#2B3440")
            hover = QColor("#8DC6FF")
            alpha = 220 if hovered else 115

        color = hover if hovered else base
        color.setAlpha(alpha)
        painter.setBrush(color)
        painter.setPen(QPen(QColor("#7D8794") if hovered else QColor("#454E5A"), 1))
        painter.drawRoundedRect(region.rect, 4, 4)

        if region.label:
            painter.setPen(QColor("#F4F7FA") if hovered else QColor("#C8D0DA"))
            painter.setFont(self._font(7 if region.key in {"left", "right"} else 8, True))
            painter.drawText(region.rect, Qt.AlignmentFlag.AlignCenter, region.label)

    def _region_at(self, position: QPointF) -> str | None:
        """Return the interactive region key under a viewport-space point."""

        if not self._regions:
            self._build_regions()

        if self._home_rect().contains(position):
            return "home"

        for region in self._regions:
            if region.rect.contains(position):
                return region.key
        return None

    def _region_by_key(self, key: str | None) -> ViewCubeRegion | None:
        """Return a region by key."""

        if key is None:
            return None

        for region in self._regions:
            if region.key == key:
                return region
        return None

    def _home_rect(self) -> QRectF:
        """Return the home button bounds."""

        return QRectF(14.0, 14.0, 60.0, 28.0)

    def _font(self, size: int, bold: bool = False) -> QFont:
        """Return the design-system-aligned ViewCube font."""

        font = QFont("Segoe UI", size)
        font.setBold(bold)
        return font

    def _lerp(self, start: float, end: float, t: float) -> float:
        """Linearly interpolate numeric values."""

        return start + (end - start) * t

    def _angle_lerp(self, start: float, end: float, t: float) -> float:
        """Interpolate angles along the shortest rotational path."""

        delta = ((end - start + 180.0) % 360.0) - 180.0
        return start + delta * t
