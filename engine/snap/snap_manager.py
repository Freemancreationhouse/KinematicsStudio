from math import sqrt

from engine.geometry import Vector2


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
            candidates.extend(self._intersection_candidates(entities))

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

    def _intersection_candidates(self, entities):

        candidates = []
        lines = [
            entity for entity in entities
            if hasattr(entity, "start") and hasattr(entity, "end")
        ]

        for index, first in enumerate(lines):
            for second in lines[index + 1:]:
                point = self._line_intersection(
                    first.start,
                    first.end,
                    second.start,
                    second.end
                )
                if point:
                    candidates.append((point, "INT", None))

        return candidates

    # ------------------------------------------------------------

    def _line_intersection(self, a1, a2, b1, b2):

        dax = a2.x - a1.x
        day = a2.y - a1.y
        dbx = b2.x - b1.x
        dby = b2.y - b1.y
        denominator = dax * dby - day * dbx

        if denominator == 0:
            return None

        dx = b1.x - a1.x
        dy = b1.y - a1.y
        t = (dx * dby - dy * dbx) / denominator
        u = (dx * day - dy * dax) / denominator

        if 0 <= t <= 1 and 0 <= u <= 1:
            return Vector2(a1.x + t * dax, a1.y + t * day)

        return None

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
