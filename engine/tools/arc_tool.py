from math import atan2, degrees, sqrt

from engine.commands import AddEntityCommand
from engine.entities import ArcEntity
from engine.geometry import Vector2
from engine.geometry.curves import angle_degrees
from engine.tools.tool import Tool


class ArcTool(Tool):
    """Create production 2D arcs using command-backed workspace updates."""

    MODES = {
        "three_point",
        "center_radius",
        "center_start_end",
        "start_center_angle",
        "start_end_radius",
    }

    def __init__(self):
        super().__init__()
        self.mode = "three_point"
        self.clockwise = False
        self.points = []
        self.preview = None
        self.numeric_text = ""
        self.status_text = "Arc: Three point"

    # --------------------------------

    def set_mode(self, mode):
        """Set construction mode."""

        if mode in self.MODES:
            self.mode = mode
            self.deactivate()

    # --------------------------------

    def deactivate(self):
        """Cancel the active arc operation."""

        self.points = []
        self.preview = None
        self.numeric_text = ""

    # --------------------------------

    def mouse_press(self, workspace, point):
        """Collect construction points and commit valid arcs."""

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
        """Support Escape, Enter, clockwise toggle and numeric angle/radius input."""

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
            return

        if key in ("C", "c"):
            self.clockwise = not self.clockwise
            self.preview = self._entity_for_points(self.points)
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            entity = self._entity_for_points(self.points)

            if entity is not None:
                workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))

            self.deactivate()
            return

        if key in ("Backspace", 0x01000003):
            self.numeric_text = self.numeric_text[:-1]
            return

        character = _key_character(key)

        if character is not None:
            self.numeric_text += character
            self.preview = self._entity_for_points(self.points)

    # --------------------------------

    def draw_preview(self, painter):
        """Draw live arc preview."""

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def _is_complete(self):
        required = {
            "three_point": 3,
            "center_radius": 2,
            "center_start_end": 3,
            "start_center_angle": 2 if self.numeric_text else 3,
            "start_end_radius": 2 if self.numeric_text else 3,
        }

        return len(self.points) >= required[self.mode]

    # --------------------------------

    def _entity_for_points(self, points):
        if self.mode == "three_point":
            return _arc_from_three_points(points, self.clockwise)
        if self.mode == "center_radius":
            return _arc_from_center_radius(points, self.clockwise)
        if self.mode == "center_start_end":
            return _arc_from_center_start_end(points, self.clockwise)
        if self.mode == "start_center_angle":
            return _arc_from_start_center_angle(points, self.numeric_text, self.clockwise)
        if self.mode == "start_end_radius":
            return _arc_from_start_end_radius(points, self.numeric_text, self.clockwise)

        return None


def _arc_from_center_radius(points, clockwise=False):
    if len(points) < 2:
        return None

    center, radius_point = points[0], points[1]
    radius = center.distance_to(radius_point)

    if radius <= 0:
        return None

    entity = ArcEntity(center.copy(), radius, 0.0, 360.0)
    entity.clockwise = clockwise

    return entity


def _arc_from_center_start_end(points, clockwise=False):
    if len(points) < 3:
        return None

    center, start, end = points[0], points[1], points[2]
    radius = center.distance_to(start)

    if radius <= 0:
        return None

    entity = ArcEntity(center.copy(), radius, angle_degrees(center, start), angle_degrees(center, end))
    entity.clockwise = clockwise

    return entity


def _arc_from_start_center_angle(points, numeric_text="", clockwise=False):
    if len(points) < 2:
        return None

    start, center = points[0], points[1]
    radius = center.distance_to(start)

    if radius <= 0:
        return None

    start_angle = angle_degrees(center, start)
    sweep = _numeric_value(numeric_text, 90.0)
    end_angle = start_angle - abs(sweep) if clockwise else start_angle + abs(sweep)
    entity = ArcEntity(center.copy(), radius, start_angle, end_angle)
    entity.clockwise = clockwise

    return entity


def _arc_from_start_end_radius(points, numeric_text="", clockwise=False):
    if len(points) < 2:
        return None

    start, end = points[0], points[1]
    chord = start.distance_to(end)
    radius = abs(_numeric_value(numeric_text, chord))

    if radius < chord * 0.5 or radius <= 0:
        radius = chord * 0.5

    midpoint = Vector2((start.x + end.x) * 0.5, (start.y + end.y) * 0.5)
    dx = end.x - start.x
    dy = end.y - start.y
    chord_length = sqrt(dx * dx + dy * dy)

    if chord_length <= 0:
        return None

    height = sqrt(max(radius * radius - (chord_length * 0.5) ** 2, 0.0))
    normal = Vector2(-dy / chord_length, dx / chord_length)

    if clockwise:
        normal = Vector2(-normal.x, -normal.y)

    center = Vector2(midpoint.x + normal.x * height, midpoint.y + normal.y * height)
    entity = ArcEntity(center, radius, angle_degrees(center, start), angle_degrees(center, end))
    entity.clockwise = clockwise

    return entity


def _arc_from_three_points(points, clockwise=False):
    if len(points) < 3:
        return None

    p1, p2, p3 = points[0], points[1], points[2]
    denominator = 2.0 * (
        p1.x * (p2.y - p3.y) +
        p2.x * (p3.y - p1.y) +
        p3.x * (p1.y - p2.y)
    )

    if abs(denominator) <= 1e-9:
        return None

    ux = (
        (p1.x * p1.x + p1.y * p1.y) * (p2.y - p3.y) +
        (p2.x * p2.x + p2.y * p2.y) * (p3.y - p1.y) +
        (p3.x * p3.x + p3.y * p3.y) * (p1.y - p2.y)
    ) / denominator
    uy = (
        (p1.x * p1.x + p1.y * p1.y) * (p3.x - p2.x) +
        (p2.x * p2.x + p2.y * p2.y) * (p1.x - p3.x) +
        (p3.x * p3.x + p3.y * p3.y) * (p2.x - p1.x)
    ) / denominator
    center = Vector2(ux, uy)
    orientation = (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
    entity = ArcEntity(center, center.distance_to(p1), angle_degrees(center, p1), angle_degrees(center, p3))
    entity.clockwise = orientation < 0 if not clockwise else True

    return entity


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
