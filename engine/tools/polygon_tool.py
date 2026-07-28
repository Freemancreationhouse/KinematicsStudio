from math import atan2, cos, degrees, pi, sin

from engine.commands import AddEntityCommand
from engine.entities import PolygonEntity
from engine.geometry import Vector2
from engine.tools.tool import Tool


class PolygonTool(Tool):
    """Create regular polygons through command-backed workspace updates."""

    def __init__(self):
        super().__init__()
        self.mode = "center"
        self.sides = 6
        self.inscribed = True
        self.points = []
        self.preview = None
        self.numeric_text = ""
        self.status_text = "Polygon: Center"

    # --------------------------------

    def set_mode(self, mode):
        """Set construction mode: center or edge."""

        if mode in ("center", "edge"):
            self.mode = mode
            self.deactivate()

    # --------------------------------

    def deactivate(self):
        """Cancel the active polygon operation."""

        self.points = []
        self.preview = None
        self.numeric_text = ""

    # --------------------------------

    def mouse_press(self, workspace, point):
        """Collect construction points and commit completed polygons."""

        self.points.append(Vector2(point.x, point.y))
        entity = self._entity_for_points(self.points)

        if entity is not None and self._is_complete():
            workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
            self.deactivate()
        else:
            self.preview = entity

    # --------------------------------

    def mouse_move(self, workspace, point):
        """Update live polygon preview."""

        if not self.points:
            return

        self.preview = self._entity_for_points(self.points + [Vector2(point.x, point.y)])

    # --------------------------------

    def mouse_release(self, workspace, point):
        """Mouse release is intentionally non-mutating."""

    # --------------------------------

    def key_press(self, workspace, key):
        """Support Escape, Enter, side count input and inscribed/circumscribed toggle."""

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
            return

        if key in ("I", "i"):
            self.inscribed = True
            self.preview = self._entity_for_points(self.points)
            return

        if key in ("C", "c"):
            self.inscribed = False
            self.preview = self._entity_for_points(self.points)
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            if self.numeric_text and not self.points:
                self.sides = _side_count(self.numeric_text, self.sides)
                self.numeric_text = ""
                return

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

            if not self.points:
                self.sides = _side_count(self.numeric_text, self.sides)
            else:
                self.preview = self._entity_for_points(self.points)

    # --------------------------------

    def draw_preview(self, painter):
        """Draw live polygon preview."""

        if self.preview:
            self.preview.draw(painter)

    # --------------------------------

    def _is_complete(self):
        return len(self.points) >= 2

    # --------------------------------

    def _entity_for_points(self, points):
        sides = _side_count(self.numeric_text, self.sides) if self.numeric_text and not self.points else self.sides

        if self.mode == "edge":
            return _edge_polygon(points, sides, self.inscribed)

        return _center_polygon(points, sides, self.inscribed)


def _center_polygon(points, sides, inscribed=True):
    if len(points) < 2:
        return None

    center, radius_point = points[0], points[1]
    radius = center.distance_to(radius_point)

    if radius <= 0:
        return None

    if not inscribed:
        radius = radius / max(cos(pi / sides), 1e-9)

    rotation = degrees(atan2(radius_point.y - center.y, radius_point.x - center.x))

    return PolygonEntity(center.copy(), radius, sides, rotation, "Inscribed" if inscribed else "Circumscribed")


def _edge_polygon(points, sides, inscribed=True):
    if len(points) < 2:
        return None

    start, end = points[0], points[1]
    edge = start.distance_to(end)

    if edge <= 0:
        return None

    radius = edge / (2.0 * max(sin(pi / sides), 1e-9))
    midpoint = Vector2((start.x + end.x) * 0.5, (start.y + end.y) * 0.5)
    dx = end.x - start.x
    dy = end.y - start.y
    edge_angle = atan2(dy, dx)
    height = (radius * radius - (edge * 0.5) ** 2) ** 0.5
    normal = Vector2(-dy / edge, dx / edge)
    center = Vector2(midpoint.x + normal.x * height, midpoint.y + normal.y * height)
    rotation = degrees(edge_angle) - 180.0 / sides

    return PolygonEntity(center, radius, sides, rotation, "Edge Inscribed" if inscribed else "Edge Circumscribed")


def _side_count(text, fallback):
    try:
        return max(3, min(360, int(float(text))))
    except (TypeError, ValueError):
        return fallback


def _key_character(key):
    key_text = str(key)

    if len(key_text) == 1 and key_text.isdigit():
        return key_text

    if isinstance(key, int) and 48 <= key <= 57:
        return chr(key)

    return None
