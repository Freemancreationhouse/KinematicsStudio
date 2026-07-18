from dataclasses import dataclass

from engine.geometry import Vector3


@dataclass
class SnapResult3D:
    """Resolved 3D snap result for preview, rendering and precision placement."""

    point: Vector3
    mode: str
    entity: object = None
    distance: float = 0.0
    priority: int = 100


class SnapManager3D:
    """Reusable 3D snap manager for scene entities, primitives and transforms."""

    DEFAULT_FILTERS = {
        "VERTEX",
        "EDGE",
        "FACE_CENTER",
        "FACE_CORNER",
        "FACE_MIDPOINT",
        "OBJECT_CENTER",
        "GRID",
        "AXIS",
        "ORIGIN",
        "INTERSECTION",
        "NEAREST",
    }
    PRIORITY = {
        "ORIGIN": 0,
        "VERTEX": 10,
        "FACE_CORNER": 12,
        "FACE_MIDPOINT": 18,
        "FACE_CENTER": 20,
        "OBJECT_CENTER": 25,
        "EDGE": 30,
        "AXIS": 35,
        "GRID": 40,
        "NEAREST": 50,
        "INTERSECTION": 60,
    }

    def __init__(self):

        self.enabled = True
        self.tolerance = 12.0
        self.grid_spacing = 50.0
        self.axis_tolerance = 10.0
        self.filters = set(self.DEFAULT_FILTERS)
        self.active_snap = None
        self.highlighted_entity = None
        self.candidates = []

    # --------------------------------

    def snap_ray(self, workspace, ray, camera=None):
        """Resolve the best visible snap candidate near a camera ray."""

        if not self.enabled:
            self.clear_preview()
            return None

        self.candidates = self.candidate_points(workspace)
        result = self._best_for_ray(ray, self.candidates)
        self._set_active(result)

        return result

    # --------------------------------

    def snap_point(self, workspace, point):
        """Resolve the best snap candidate near a world-space point."""

        if not self.enabled:
            return point

        self._workspace_coordinate_manager = getattr(
            workspace,
            "coordinate_system_manager",
            None,
        )
        candidates = self.candidate_points(workspace)

        if not candidates:
            return self._grid_point(point).point if self._filter_enabled("GRID") else point

        result = min(
            candidates,
            key=lambda item: (
                item.point.distance_to(point),
                item.priority,
            ),
        )

        if result.point.distance_to(point) <= self.world_tolerance:
            self._set_active(result)
            return result.point

        if self._filter_enabled("GRID"):
            result = self._grid_point(point)
            self._set_active(result)
            return result.point

        return point

    # --------------------------------

    def candidate_points(self, workspace):
        """Return snap candidates from visible 3D entities and foundation aids."""

        candidates = []

        for entity in self._visible_entities(workspace):
            candidates.extend(self._entity_candidates(entity))

        candidates.extend(self._foundation_candidates())

        return candidates

    # --------------------------------

    def set_enabled(self, enabled):
        """Enable or disable all 3D snapping."""

        self.enabled = bool(enabled)

        if not self.enabled:
            self.clear_preview()

    # --------------------------------

    def set_filter(self, mode, enabled):
        """Enable or disable a snap filter by mode name."""

        mode = self._mode(mode)

        if enabled:
            self.filters.add(mode)
        else:
            self.filters.discard(mode)

    # --------------------------------

    def clear_preview(self):
        """Clear transient snap preview state."""

        self.active_snap = None
        self.highlighted_entity = None
        self.candidates = []

    # --------------------------------

    @property
    def world_tolerance(self):
        """Return coarse world-space tolerance for non-camera placement calls."""

        return max(float(self.tolerance), 1.0)

    # --------------------------------

    def to_dict(self):
        """Return JSON-safe snap settings."""

        return {
            "enabled": self.enabled,
            "tolerance": self.tolerance,
            "grid_spacing": self.grid_spacing,
            "axis_tolerance": self.axis_tolerance,
            "filters": sorted(self.filters),
        }

    # --------------------------------

    def from_dict(self, data):
        """Restore snap settings from persisted data."""

        data = data or {}
        self.enabled = bool(data.get("enabled", self.enabled))
        self.tolerance = float(data.get("tolerance", self.tolerance))
        self.grid_spacing = float(data.get("grid_spacing", self.grid_spacing))
        self.axis_tolerance = float(data.get("axis_tolerance", self.axis_tolerance))
        self.filters = set(data.get("filters", sorted(self.DEFAULT_FILTERS)))

    # --------------------------------

    def _entity_candidates(self, entity):

        candidates = []
        points = list(entity.points())

        if self._filter_enabled("VERTEX"):
            candidates.extend(
                self._result(point, "VERTEX", entity)
                for point in points
            )

        if self._filter_enabled("FACE_CORNER"):
            candidates.extend(
                self._result(point, "FACE_CORNER", entity)
                for point in points
            )

        if self._filter_enabled("OBJECT_CENTER"):
            box = getattr(entity, "bounding_box3d", None)

            if box is not None and box.valid:
                candidates.append(self._result(box.center, "OBJECT_CENTER", entity))

        segments = list(entity.segments())

        if self._filter_enabled("FACE_MIDPOINT") or self._filter_enabled("EDGE"):
            for start, end in segments:
                midpoint = (start + end) * 0.5

                if self._filter_enabled("FACE_MIDPOINT"):
                    candidates.append(self._result(midpoint, "FACE_MIDPOINT", entity))

                if self._filter_enabled("EDGE"):
                    candidates.append(self._result(midpoint, "EDGE", entity))

        if self._filter_enabled("FACE_CENTER") and hasattr(entity, "triangles"):
            for triangle in entity.triangles():
                center = (triangle[0] + triangle[1] + triangle[2]) / 3.0
                candidates.append(self._result(center, "FACE_CENTER", entity))

        if self._filter_enabled("NEAREST"):
            candidates.extend(
                self._result(point, "NEAREST", entity)
                for point in points
            )

        return candidates

    # --------------------------------

    def _foundation_candidates(self):

        candidates = []

        if self._filter_enabled("ORIGIN"):
            candidates.append(self._result(Vector3(), "ORIGIN"))

        if self._filter_enabled("AXIS"):
            size = self.grid_spacing
            candidates.extend([
                self._result(Vector3(size, 0.0, 0.0), "AXIS"),
                self._result(Vector3(0.0, size, 0.0), "AXIS"),
                self._result(Vector3(0.0, 0.0, size), "AXIS"),
            ])

        return candidates

    # --------------------------------

    def _best_for_ray(self, ray, candidates):

        if not candidates:
            return None

        scored = []

        for candidate in candidates:
            distance = _ray_point_distance(ray, candidate.point)

            if distance <= self.tolerance:
                scored.append(SnapResult3D(
                    candidate.point,
                    candidate.mode,
                    candidate.entity,
                    distance,
                    candidate.priority,
                ))

        if not scored:
            return None

        return min(scored, key=lambda item: (item.priority, item.distance))

    # --------------------------------

    def _grid_point(self, point):

        coordinate_manager = getattr(self, "_workspace_coordinate_manager", None)
        active_system = getattr(coordinate_manager, "active", None)
        coordinate_spacing = (
            getattr(coordinate_manager, "grid_spacing", self.grid_spacing)
            if coordinate_manager is not None else self.grid_spacing
        )
        requested_spacing = (
            self.grid_spacing
            if self.grid_spacing != 50.0
            else coordinate_spacing
        )
        spacing = max(float(requested_spacing), 0.0001)

        if active_system is not None:
            local = active_system.from_world(point)

            return self._result(
                active_system.to_world(Vector3(
                    round(local.x / spacing) * spacing,
                    round(local.y / spacing) * spacing,
                    round(local.z / spacing) * spacing,
                )),
                "GRID",
            )

        return self._result(
            Vector3(
                round(point.x / spacing) * spacing,
                round(point.y / spacing) * spacing,
                round(point.z / spacing) * spacing,
            ),
            "GRID",
        )

    # --------------------------------

    def _set_active(self, result):

        self.active_snap = result
        self.highlighted_entity = result.entity if result else None

    # --------------------------------

    def _result(self, point, mode, entity=None, distance=0.0):

        mode = self._mode(mode)

        return SnapResult3D(
            point,
            mode,
            entity,
            distance,
            self.PRIORITY.get(mode, 100),
        )

    # --------------------------------

    def _filter_enabled(self, mode):

        return self._mode(mode) in self.filters

    # --------------------------------

    def _mode(self, mode):

        return str(mode or "").upper()

    # --------------------------------

    def _visible_entities(self, workspace):

        self._workspace_coordinate_manager = getattr(
            workspace,
            "coordinate_system_manager",
            None,
        )

        if hasattr(workspace, "visible_3d_entities"):
            return workspace.visible_3d_entities()

        scene = getattr(workspace, "scene3d", None)

        return scene.visible_entities() if scene is not None else []


def _ray_point_distance(ray, point):

    offset = point - ray.origin
    along = max(0.0, offset.dot(ray.direction))
    closest = ray.point_at(along)

    return closest.distance_to(point)
