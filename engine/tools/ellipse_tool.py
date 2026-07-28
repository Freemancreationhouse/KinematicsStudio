from math import atan2, degrees

from engine.commands import AddEntityCommand
from engine.entities import EllipseEntity
from engine.geometry import Vector2
from engine.tools.tool import Tool


class EllipseTool(Tool):
    """Create editable ellipses through the existing command system."""

    def __init__(self):
        super().__init__()
        self.mode = "center"
        self.points = []
        self.preview = None
        self.numeric_text = ""
        self.status_text = "Ellipse: Center"

    # --------------------------------

    def set_mode(self, mode):
        """Set ellipse mode: center or axis."""

        if mode in ("center", "axis"):
            self.mode = mode
            self.deactivate()

    # --------------------------------

    def deactivate(self):
        """Cancel current ellipse construction."""

        self.points = []
        self.preview = None
        self.numeric_text = ""

    # --------------------------------

    def mouse_press(self, workspace, point):
        """Collect construction points and commit completed ellipses."""

        self.points.append(Vector2(point.x, point.y))
        entity = self._entity_for_points(self.points)

        if entity is not None and self._is_complete():
            workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
            self.deactivate()
        else:
            self.preview = entity

    # --------------------------------

    def mouse_move(self, workspace, point):
        """Update dynamic preview."""

        if not self.points:
            return

        self.preview = self._entity_for_points(self.points + [Vector2(point.x, point.y)])

    # --------------------------------

    def mouse_release(self, workspace, point):
        """Mouse release is intentionally non-mutating."""

    # --------------------------------

    def key_press(self, workspace, key):
        """Support Escape, Enter and numeric minor-axis input."""

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            entity = self._entity_for_points(self.points)

            if entity is not None:
                workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))

            self.deactivate()
            return

        if key in ("Backspace", 0x01000003):
            self.numeric_text = self.numeric_text[:-1]
            self.preview = self._entity_for_points(self.points)
            return

        character = _key_character(key)

        if character is not None:
            self.numeric_text += character
            self.preview = self._entity_for_points(self.points)

    # --------------------------------

    def draw_preview(self, painter):
        """Draw live ellipse preview."""

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def _is_complete(self):
        return len(self.points) >= 2 if self.numeric_text else len(self.points) >= 3

    # --------------------------------

    def _entity_for_points(self, points):
        if self.mode == "axis":
            return _axis_ellipse(points, self.numeric_text)

        return _center_ellipse(points, self.numeric_text)


def _center_ellipse(points, numeric_text=""):
    if len(points) < 2:
        return None

    center = points[0]
    major_point = points[1]
    radius_x = center.distance_to(major_point)

    if radius_x <= 0:
        return None

    rotation = degrees(atan2(major_point.y - center.y, major_point.x - center.x))

    if numeric_text:
        radius_y = abs(_numeric_value(numeric_text, radius_x))
    elif len(points) >= 3:
        radius_y = _minor_radius_from_point(center, major_point, points[2])
    else:
        radius_y = radius_x

    if radius_y <= 0:
        return None

    return EllipseEntity(center.copy(), radius_x, radius_y, rotation)


def _axis_ellipse(points, numeric_text=""):
    if len(points) < 2:
        return None

    axis_start, axis_end = points[0], points[1]
    center = Vector2((axis_start.x + axis_end.x) * 0.5, (axis_start.y + axis_end.y) * 0.5)
    radius_x = axis_start.distance_to(axis_end) * 0.5

    if radius_x <= 0:
        return None

    rotation = degrees(atan2(axis_end.y - axis_start.y, axis_end.x - axis_start.x))

    if numeric_text:
        radius_y = abs(_numeric_value(numeric_text, radius_x))
    elif len(points) >= 3:
        radius_y = _minor_radius_from_point(center, axis_end, points[2])
    else:
        radius_y = radius_x

    if radius_y <= 0:
        return None

    return EllipseEntity(center, radius_x, radius_y, rotation)


def _minor_radius_from_point(center, major_point, point):
    dx = major_point.x - center.x
    dy = major_point.y - center.y
    length = (dx * dx + dy * dy) ** 0.5

    if length <= 0:
        return 0.0

    nx = -dy / length
    ny = dx / length

    return abs((point.x - center.x) * nx + (point.y - center.y) * ny)


def _numeric_value(text, fallback):
    try:
        return float(text)
    except (TypeError, ValueError):
        return fallback


def _key_character(key):
    key_text = str(key)

    if len(key_text) == 1 and (key_text.isdigit() or key_text in ".-"):
        return key_text

    if isinstance(key, int):
        if 48 <= key <= 57:
            return chr(key)
        if key == 46:
            return "."
        if key == 45:
            return "-"

    return None
