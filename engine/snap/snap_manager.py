from math import sqrt

from engine.geometry import Vector2
from engine.geometry.curves import midpoint, nearest_on_curve, polyline_segments
from engine.geometry.primitives import segment_intersection


class SnapResult:
    """Represents the resolved snap point and snap mode."""

    def __init__(self, point, mode="OFF", entity=None, distance=float("inf")):

        self.point = point
        self.mode = mode
        self.entity = entity
        self.distance = distance


class SnapManager:
    """Finds object and grid snap targets for visible workspace entities."""

    def __init__(self):

        self.enabled = True
        self.endpoint = True
        self.midpoint = True
        self.center = True
        self.intersection = True
        self.nearest = True
        self.quadrant = True
        self.grid = True
        self.grid_size = 25
        self.tolerance = 12
        self.current = SnapResult(Vector2(), "OFF")

    # ------------------------------------------------------------

    def toggle(self):

        self.enabled = not self.enabled
        if not self.enabled:
            self.current = SnapResult(self.current.point, "OFF")
        return self.enabled

    # ------------------------------------------------------------

    def snap(self, point, workspace, camera=None):

        if not self.enabled:
            self.current = SnapResult(point.copy(), "OFF")
            return self.current

        tolerance = self._world_tolerance(camera)
        candidates = []
        entities = (
            workspace.snap_candidates()
            if hasattr(workspace, "snap_candidates")
            else [
                entity for entity in getattr(workspace, "entities", [])
                if getattr(entity, "visible", True)
            ]
        )

        for entity in entities:
            candidates.extend(self._entity_candidates(entity, point))

        if self.intersection:
            candidates.extend(self._intersection_candidates(entities, point, tolerance))

        if self.grid:
            candidates.append((self._grid_point(point), "GRID", None))

        best = SnapResult(point.copy(), "OFF")
        best_score = float("inf")

        for candidate, mode, entity in candidates:
            distance = point.distance_to(candidate)
            score = distance + self._priority_offset(mode, tolerance)

            if distance <= tolerance and score < best_score:
                best = SnapResult(candidate.copy(), mode, entity, distance)
                best_score = score

        self.current = best
        return best

    # ------------------------------------------------------------

    def _entity_candidates(self, entity, point):

        candidates = []

        if hasattr(entity, "start") and hasattr(entity, "end"):
            candidates.extend(self._line_candidates(entity, point))

        elif hasattr(entity, "p1") and hasattr(entity, "p2"):
            candidates.extend(self._rectangle_candidates(entity, point))

        elif hasattr(entity, "center") and hasattr(entity, "radius"):
            candidates.extend(self._circle_candidates(entity, point))

        elif hasattr(entity, "points"):
            candidates.extend(self._curve_candidates(entity, entity.points, point, getattr(entity, "closed", False)))

        elif hasattr(entity, "control_points"):
            candidates.extend(self._curve_candidates(entity, entity.control_points, point, False))

        return candidates

    # ------------------------------------------------------------

    def _line_candidates(self, entity, point):

        candidates = []

        if self.endpoint:
            candidates.append((entity.start, "END", entity))
            candidates.append((entity.end, "END", entity))

        if self.midpoint:
            candidates.append((self._midpoint(entity.start, entity.end), "MID", entity))

        if self.nearest:
            candidates.append((self._nearest_on_segment(point, entity.start, entity.end), "NEAR", entity))

        return candidates

    # ------------------------------------------------------------

    def _rectangle_candidates(self, entity, point):

        candidates = []
        corners = self._rectangle_corners(entity)

        if self.endpoint:
            for corner in corners:
                candidates.append((corner, "END", entity))

        if self.midpoint:
            for a, b in zip(corners, corners[1:] + corners[:1]):
                candidates.append((self._midpoint(a, b), "MID", entity))

        if self.center:
            candidates.append((self._midpoint(entity.p1, entity.p2), "CENTER", entity))

        if self.nearest:
            nearest = self._nearest_on_edges(point, corners)
            if nearest:
                candidates.append((nearest, "NEAR", entity))

        return candidates

    # ------------------------------------------------------------

    def _circle_candidates(self, entity, point):

        candidates = []

        if self.center:
            candidates.append((entity.center, "CENTER", entity))

        if self.quadrant:
            r = entity.radius
            candidates.extend([
                (Vector2(entity.center.x + r, entity.center.y), "QUAD", entity),
                (Vector2(entity.center.x - r, entity.center.y), "QUAD", entity),
                (Vector2(entity.center.x, entity.center.y + r), "QUAD", entity),
                (Vector2(entity.center.x, entity.center.y - r), "QUAD", entity),
            ])

        nearest = self._nearest_on_circle(point, entity)

        if nearest:
            candidates.append((nearest, "NEAR", entity))

        return candidates

    # ------------------------------------------------------------

    def _curve_candidates(self, entity, points, point, closed=False):

        candidates = []

        if self.endpoint:
            for vertex in points:
                candidates.append((vertex, "END", entity))

        if self.midpoint:
            for start, end in polyline_segments(points, closed):
                candidates.append((midpoint(start, end), "MID", entity))

        if self.nearest:
            nearest = nearest_on_curve(point, points, closed)

            if nearest is not None:
                candidates.append((nearest, "NEAR", entity))

        return candidates

    # ------------------------------------------------------------

    def _nearest_on_edges(self, point, corners):

        nearest = None
        best = float("inf")

        for a, b in zip(corners, corners[1:] + corners[:1]):
            candidate = self._nearest_on_segment(point, a, b)
            distance = point.distance_to(candidate)
            if distance < best:
                best = distance
                nearest = candidate

        return nearest

    # ------------------------------------------------------------

    def _nearest_on_circle(self, point, entity):

        if not self.nearest or entity.radius <= 0:
            return None

        dx = point.x - entity.center.x
        dy = point.y - entity.center.y
        length = sqrt(dx * dx + dy * dy)

        if not length:
            return None

        return Vector2(
            entity.center.x + dx / length * entity.radius,
            entity.center.y + dy / length * entity.radius
        )

    # ------------------------------------------------------------

    def _intersection_candidates(self, entities, point=None, tolerance=None):

        candidates = []
        segments = []

        for entity in entities:
            if hasattr(entity, "start") and hasattr(entity, "end"):
                segments.append((entity.start, entity.end))
            elif hasattr(entity, "points"):
                segments.extend(polyline_segments(entity.points, getattr(entity, "closed", False)))
            elif hasattr(entity, "control_points"):
                segments.extend(polyline_segments(entity.sampled_points()))

        if point is not None and tolerance is not None:
            segments = [
                segment for segment in segments
                if self._segment_near_point(segment, point, tolerance)
            ]

        for index, first in enumerate(segments):
            for second in segments[index + 1:]:
                point = segment_intersection(first[0], first[1], second[0], second[1])

                if point:
                    candidates.append((point, "INT", None))

        return candidates

    # ------------------------------------------------------------

    def _segment_near_point(self, segment, point, tolerance):

        start, end = segment

        return not (
            max(start.x, end.x) < point.x - tolerance or
            min(start.x, end.x) > point.x + tolerance or
            max(start.y, end.y) < point.y - tolerance or
            min(start.y, end.y) > point.y + tolerance
        )

    # ------------------------------------------------------------

    def _grid_point(self, point):

        return Vector2(
            round(point.x / self.grid_size) * self.grid_size,
            round(point.y / self.grid_size) * self.grid_size
        )

    # ------------------------------------------------------------

    def _rectangle_corners(self, entity):

        x1 = entity.p1.x
        y1 = entity.p1.y
        x2 = entity.p2.x
        y2 = entity.p2.y

        return [
            Vector2(x1, y1),
            Vector2(x2, y1),
            Vector2(x2, y2),
            Vector2(x1, y2),
        ]

    # ------------------------------------------------------------

    def _midpoint(self, a, b):

        return Vector2((a.x + b.x) * 0.5, (a.y + b.y) * 0.5)

    # ------------------------------------------------------------

    def _nearest_on_segment(self, point, a, b):

        dx = b.x - a.x
        dy = b.y - a.y
        length_squared = dx * dx + dy * dy

        if length_squared == 0:
            return a.copy()

        t = ((point.x - a.x) * dx + (point.y - a.y) * dy) / length_squared
        t = max(0.0, min(1.0, t))

        return Vector2(a.x + t * dx, a.y + t * dy)

    # ------------------------------------------------------------

    def _world_tolerance(self, camera):

        if camera is None:
            return self.tolerance

        return self.tolerance / max(camera.zoom, 0.01)

    # ------------------------------------------------------------

    def _priority_offset(self, mode, tolerance):

        if mode == "INT":
            return -tolerance * 0.1

        if mode in ("END", "MID", "CENTER", "QUAD"):
            return 0.0

        if mode == "NEAR":
            return tolerance * 0.25

        if mode == "GRID":
            return tolerance * 0.5

        return tolerance
