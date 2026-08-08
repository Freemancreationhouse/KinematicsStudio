from __future__ import annotations

from math import sqrt
from typing import Any

from engine.geometry import Vector2, Vector3
from engine.geometry.curves import midpoint, nearest_on_curve, polyline_segments
from engine.geometry.primitives import segment_intersection
from engine.snapping.snapping_cache import SnappingCache
from engine.snapping.snapping_context import SnappingContext
from engine.snapping.snapping_events import SnappingEvents
from engine.snapping.snapping_filter import SnappingFilter
from engine.snapping.snapping_grid import SnappingGrid
from engine.snapping.snapping_marker import SnappingMarker
from engine.snapping.snapping_priority import SnappingPriority
from engine.snapping.snapping_result import SnappingResult
from engine.snapping.snapping_session import SnappingSession
from engine.snapping.snapping_settings import SnappingSettings
from engine.snapping.snapping_target import (
    SnappingTarget,
    SnappingTargetCategory,
    SnappingTargetType,
)


class SnappingManager:
    """Professional CAD snapping engine for current and future tools."""

    def __init__(
        self,
        settings: SnappingSettings | None = None,
        priority: SnappingPriority | None = None,
        filters: SnappingFilter | None = None,
    ) -> None:
        """Create a reusable snapping manager."""

        self.settings = settings or SnappingSettings()
        self.priority = priority or SnappingPriority()
        self.filters = filters or SnappingFilter()
        self.events = SnappingEvents()
        self.cache = SnappingCache()
        self.grid = SnappingGrid(self.settings.grid_spacing)
        self.active_result = SnappingResult.off()
        self.active_marker: SnappingMarker | None = None
        self._sessions: dict[str, SnappingSession] = {}
        self._ai_requests: list[dict[str, Any]] = []

    def start_session(self, workspace: Any) -> SnappingSession:
        """Begin a snapping session for a workspace."""

        session = SnappingSession(workspace)
        self._sessions[session.session_id] = session
        self.events.emit("SnappingSessionStarted", session.session_id, {})
        return session

    def end_session(self, session_id: str) -> None:
        """End and remove a snapping session."""

        session = self._sessions.pop(str(session_id), None)
        if session is None:
            return
        session.finish()
        self.events.emit("SnappingSessionEnded", session.session_id, {})

    def snap(
        self,
        point: Any,
        workspace: Any,
        camera: Any = None,
        session_id: str | None = None,
    ) -> SnappingResult:
        """Resolve the best snap result near a point."""

        world_point = _to_vector3(point)
        if not self.settings.enabled:
            return self._set_active(SnappingResult.off(world_point), session_id)

        context = SnappingContext.from_workspace(
            workspace,
            world_point,
            camera=camera,
            settings=self.settings,
            filters=self.filters,
        )
        candidates = self.candidates(context)
        result = self._best_result(context, candidates)
        return self._set_active(result, session_id)

    def snap_point(self, workspace: Any, point: Any) -> Vector3:
        """Compatibility helper returning only the resolved point."""

        return self.snap(point, workspace).point

    def candidates(self, context: SnappingContext) -> list[SnappingTarget]:
        """Return all enabled snap candidates for a context."""

        revision = self._workspace_revision(context.workspace)
        if self.cache.valid_for(context.workspace, revision):
            targets = list(self.cache.targets)
        else:
            targets = self._workspace_targets(context.workspace)
            self.cache.store(context.workspace, targets, revision)

        transient = self._transient_targets(context)
        return [
            target
            for target in [*targets, *transient]
            if self._target_enabled(target)
        ]

    def marker(self) -> SnappingMarker | None:
        """Return current visual marker metadata."""

        return self.active_marker

    def clear(self) -> None:
        """Clear active snap state and cached targets."""

        self.active_result = SnappingResult.off()
        self.active_marker = None
        self.cache.clear()
        self.events.emit("SnappingCleared", "", {})

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable snapping."""

        self.settings.enabled = bool(enabled)
        if not self.settings.enabled:
            self.clear()
        self.events.emit("SnappingEnabledChanged", "", {"enabled": self.settings.enabled})

    def set_priority(self, target_type: SnappingTargetType | str, priority: int) -> None:
        """Configure one target type priority."""

        self.priority.set_priority(target_type, priority)
        self.events.emit("SnappingPriorityChanged", "", {"target_type": str(target_type)})

    def set_filter(self, target_type: SnappingTargetType | str, enabled: bool) -> None:
        """Enable or disable one target type filter."""

        if enabled:
            self.filters.enable_target_type(target_type)
        else:
            self.filters.disable_target_type(target_type)
        self.events.emit(
            "SnappingFilterChanged",
            "",
            {"target_type": str(target_type), "enabled": bool(enabled)},
        )

    def request_ai_snap(
        self,
        mode: SnappingTargetType | str,
        *,
        point: Any | None = None,
        target_ids: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an AI snap request without editing geometry."""

        request = {
            "mode": _target_type(mode).value,
            "point": _vector_to_data(_to_vector3(point)) if point is not None else None,
            "target_ids": tuple(target_ids),
            "metadata": dict(metadata or {}),
        }
        self._ai_requests.append(request)
        self.events.emit("SnappingAIRequestRecorded", "", request)
        return request

    def ai_requests(self) -> tuple[dict[str, Any], ...]:
        """Return recorded AI snapping integration requests."""

        return tuple(dict(request) for request in self._ai_requests)

    def _workspace_targets(self, workspace: Any) -> list[SnappingTarget]:
        """Collect persistent snap targets from workspace state."""

        targets: list[SnappingTarget] = []
        entities = self._visible_entities(workspace)
        for entity in entities:
            targets.extend(self._entity_targets(entity))
        targets.extend(self._intersection_targets(entities))
        return targets

    def _transient_targets(self, context: SnappingContext) -> list[SnappingTarget]:
        """Collect context-specific snap targets."""

        targets: list[SnappingTarget] = []
        if self.settings.snap_to_grid:
            targets.append(
                SnappingTarget(
                    self.grid.snap(context.point),
                    SnappingTargetType.GRID,
                    category=SnappingTargetCategory.GRID,
                    label="Grid",
                )
            )
        if self.settings.snap_to_origin:
            targets.append(
                SnappingTarget(
                    Vector3(),
                    SnappingTargetType.ORIGIN,
                    category=SnappingTargetCategory.GRID,
                    label="Origin",
                )
            )
        selection_center = self._selection_center(context.selection_manager)
        if selection_center is not None:
            targets.append(
                SnappingTarget(
                    selection_center,
                    SnappingTargetType.SELECTION_CENTER,
                    category=SnappingTargetCategory.REFERENCE,
                    label="Selection Center",
                )
            )
        return targets

    def _entity_targets(self, entity: Any) -> list[SnappingTarget]:
        """Collect snap targets from one visible entity."""

        targets: list[SnappingTarget] = []
        points = self._entity_points(entity)
        segments = self._entity_segments(entity, points)
        center_only = bool(
            hasattr(entity, "center")
            and not segments
            and len(points) == 1
        )

        if not center_only:
            for point in points:
                targets.append(self._target(point, SnappingTargetType.ENDPOINT, entity, SnappingTargetCategory.VERTICES))
                targets.append(self._target(point, SnappingTargetType.REFERENCE_VERTEX, entity, SnappingTargetCategory.REFERENCE))

        for start, end in segments:
            mid = _midpoint3(start, end)
            targets.append(self._target(mid, SnappingTargetType.MIDPOINT, entity, SnappingTargetCategory.EDGES))
            targets.append(self._target(mid, SnappingTargetType.REFERENCE_EDGE, entity, SnappingTargetCategory.REFERENCE))

        center = self._entity_center(entity, points)
        if center is not None:
            targets.append(self._target(center, SnappingTargetType.CENTER, entity))
            targets.append(self._target(center, SnappingTargetType.BODY_CENTER, entity, SnappingTargetCategory.BODIES))
            targets.append(self._target(center, SnappingTargetType.BOUNDING_BOX_CENTER, entity, SnappingTargetCategory.BODIES))

        if hasattr(entity, "center") and hasattr(entity, "radius"):
            targets.extend(self._quadrant_targets(entity))

        if segments:
            for start, end in segments:
                nearest = _midpoint3(start, end)
                targets.append(self._target(nearest, SnappingTargetType.NEAREST, entity, SnappingTargetCategory.EDGES))
                targets.append(self._target(nearest, SnappingTargetType.PERPENDICULAR, entity, SnappingTargetCategory.EDGES))
                targets.append(self._target(nearest, SnappingTargetType.PARALLEL, entity, SnappingTargetCategory.EDGES))
                targets.append(self._target(nearest, SnappingTargetType.TANGENT, entity, SnappingTargetCategory.EDGES))

        if getattr(entity, "construction", False):
            for point in points:
                targets.append(self._target(point, SnappingTargetType.CONSTRUCTION_POINT, entity, SnappingTargetCategory.CONSTRUCTION))
            for start, end in segments:
                targets.append(self._target(_midpoint3(start, end), SnappingTargetType.CONSTRUCTION_LINE, entity, SnappingTargetCategory.CONSTRUCTION))

        return targets

    def _intersection_targets(self, entities: list[Any]) -> list[SnappingTarget]:
        """Collect 2D projected segment intersections."""

        segments: list[tuple[Vector3, Vector3, Any]] = []
        for entity in entities:
            for start, end in self._entity_segments(entity, self._entity_points(entity)):
                segments.append((start, end, entity))

        targets: list[SnappingTarget] = []
        for index, first in enumerate(segments):
            for second in segments[index + 1:]:
                point = segment_intersection(
                    Vector2(first[0].x, first[0].y),
                    Vector2(first[1].x, first[1].y),
                    Vector2(second[0].x, second[0].y),
                    Vector2(second[1].x, second[1].y),
                )
                if point is not None:
                    targets.append(
                        SnappingTarget(
                            Vector3(point.x, point.y, 0.0),
                            SnappingTargetType.INTERSECTION,
                            source=(first[2], second[2]),
                            category=SnappingTargetCategory.GEOMETRY,
                            label="Intersection",
                        )
                    )
        return targets

    def _quadrant_targets(self, entity: Any) -> list[SnappingTarget]:
        """Return circle-like quadrant snap targets."""

        center = _to_vector3(getattr(entity, "center"))
        radius = float(getattr(entity, "radius", 0.0))
        if radius <= 0.0:
            return []
        return [
            self._target(Vector3(center.x + radius, center.y, center.z), SnappingTargetType.QUADRANT, entity),
            self._target(Vector3(center.x - radius, center.y, center.z), SnappingTargetType.QUADRANT, entity),
            self._target(Vector3(center.x, center.y + radius, center.z), SnappingTargetType.QUADRANT, entity),
            self._target(Vector3(center.x, center.y - radius, center.z), SnappingTargetType.QUADRANT, entity),
        ]

    def _best_result(
        self,
        context: SnappingContext,
        candidates: list[SnappingTarget],
    ) -> SnappingResult:
        """Return the highest-priority target within tolerance."""

        best: SnappingResult | None = None
        for target in candidates:
            distance = context.point.distance_to(target.point)
            if distance > self._world_tolerance(context.camera):
                continue
            priority = self.priority.priority(target.target_type)
            result = SnappingResult.from_target(target, distance=distance, priority=priority)
            if best is None or (result.priority, result.distance) < (best.priority, best.distance):
                best = result
        return best or SnappingResult.off(context.point.copy())

    def _set_active(
        self,
        result: SnappingResult,
        session_id: str | None = None,
    ) -> SnappingResult:
        """Store active result and emit state changes."""

        self.active_result = result
        self.active_marker = SnappingMarker.from_result(result)
        if session_id is not None and session_id in self._sessions:
            self._sessions[session_id].update(result)
        self.events.emit(
            "SnappingResolved",
            session_id or "",
            {"result": result, "marker": self.active_marker},
        )
        return result

    def _target_enabled(self, target: SnappingTarget) -> bool:
        """Return True when settings and filters allow a target."""

        return (
            target.target_type in self.settings.enabled_targets
            and self.filters.allows(target)
        )

    def _target(
        self,
        point: Vector3,
        target_type: SnappingTargetType,
        entity: Any = None,
        category: SnappingTargetCategory = SnappingTargetCategory.GEOMETRY,
    ) -> SnappingTarget:
        """Create a snap target."""

        return SnappingTarget(
            point.copy(),
            target_type,
            source=entity,
            category=category,
            label=target_type.value,
        )

    def _entity_points(self, entity: Any) -> list[Vector3]:
        """Return 3D snap points for native 3D or projected 2D entities."""

        points = getattr(entity, "points", None)
        if callable(points):
            return [_to_vector3(point) for point in points()]

        sampled = getattr(entity, "sampled_points", None)
        if callable(sampled):
            return [_to_vector3(point) for point in sampled()]

        boundary = getattr(entity, "current_boundary_points", None)
        if callable(boundary):
            return [_to_vector3(point) for point in boundary()]

        if points is not None:
            return [_to_vector3(point) for point in list(points or [])]

        if hasattr(entity, "start") and hasattr(entity, "end"):
            return [_to_vector3(entity.start), _to_vector3(entity.end)]

        if hasattr(entity, "p1") and hasattr(entity, "p2"):
            return [_to_vector3(entity.p1), _to_vector3(entity.p2)]

        if hasattr(entity, "center"):
            return [_to_vector3(entity.center)]

        if hasattr(entity, "position3d"):
            return [_to_vector3(entity.position3d)]

        if hasattr(entity, "position"):
            return [_to_vector3(entity.position)]

        return []

    def _entity_segments(
        self,
        entity: Any,
        points: list[Vector3] | None = None,
    ) -> list[tuple[Vector3, Vector3]]:
        """Return snap segments for native 3D or projected 2D entities."""

        segments = getattr(entity, "segments", None)
        if callable(segments):
            return [
                (_to_vector3(start), _to_vector3(end))
                for start, end in segments()
            ]

        if hasattr(entity, "start") and hasattr(entity, "end"):
            return [(_to_vector3(entity.start), _to_vector3(entity.end))]

        points = points if points is not None else self._entity_points(entity)
        if len(points) > 1:
            closed = bool(getattr(entity, "closed", False))
            pairs = list(zip(points, points[1:]))
            if closed:
                pairs.append((points[-1], points[0]))
            return pairs

        return []

    def _entity_center(
        self,
        entity: Any,
        points: list[Vector3],
    ) -> Vector3 | None:
        """Return best available entity center."""

        box = getattr(entity, "bounding_box3d", None)
        if box is not None and getattr(box, "valid", False):
            return _to_vector3(box.center)

        box2 = getattr(entity, "bounding_box", None)
        if box2 is not None and getattr(box2, "valid", False):
            return _to_vector3(box2.center)

        center = getattr(entity, "center", None)
        if center is not None:
            return _to_vector3(center)

        if not points:
            return None

        total = Vector3()
        for point in points:
            total = total + point
        return total / len(points)

    def _selection_center(self, selection_manager: Any) -> Vector3 | None:
        """Return active selection center when available."""

        if selection_manager is None:
            return None
        selected = getattr(selection_manager, "selected", [])
        if callable(selected):
            selected = selected()
        points: list[Vector3] = []
        for entity in list(selected or []):
            points.extend(self._entity_points(entity)[:1])
        if not points:
            return None
        total = Vector3()
        for point in points:
            total = total + point
        return total / len(points)

    def _visible_entities(self, workspace: Any) -> list[Any]:
        """Return visible workspace entities without owning model data."""

        snap_candidates = getattr(workspace, "snap_candidates", None)
        if callable(snap_candidates):
            return list(snap_candidates())

        selectable = getattr(workspace, "selectable_entities", None)
        if callable(selectable):
            return [
                entity
                for entity in selectable()
                if getattr(entity, "visible", True)
            ]

        entities = getattr(workspace, "entities", [])
        if callable(entities):
            entities = entities()
        return [
            entity
            for entity in list(entities or [])
            if getattr(entity, "visible", True)
        ]

    def _workspace_revision(self, workspace: Any) -> int | None:
        """Read a workspace revision-like value when present."""

        for name in ("revision", "version", "modified_revision"):
            value = getattr(workspace, name, None)
            if callable(value):
                try:
                    value = value()
                except TypeError:
                    continue
            if isinstance(value, int):
                return value
        return None

    def _world_tolerance(self, camera: Any) -> float:
        """Return world-space tolerance for snapping."""

        if camera is None:
            return float(self.settings.tolerance)
        zoom = getattr(camera, "zoom", None)
        if isinstance(zoom, (int, float)):
            return float(self.settings.tolerance) / max(float(zoom), 0.01)
        return float(self.settings.tolerance)


def _to_vector3(point: Any) -> Vector3:
    """Convert a 2D or 3D point-like object to Vector3."""

    if isinstance(point, Vector3):
        return point.copy()
    if hasattr(point, "z"):
        return Vector3(float(point.x), float(point.y), float(point.z))
    return Vector3(float(getattr(point, "x", 0.0)), float(getattr(point, "y", 0.0)), 0.0)


def _midpoint3(start: Vector3, end: Vector3) -> Vector3:
    """Return midpoint between two Vector3 values."""

    return (start + end) * 0.5


def _target_type(value: SnappingTargetType | str) -> SnappingTargetType:
    """Normalize target type values."""

    if isinstance(value, SnappingTargetType):
        return value
    text = str(value)
    for target_type in SnappingTargetType:
        if text.upper() in (target_type.name.upper(), target_type.value.upper()):
            return target_type
    return SnappingTargetType.NEAREST


def _vector_to_data(vector: Vector3) -> dict[str, float]:
    """Return JSON-safe vector data."""

    return {"x": vector.x, "y": vector.y, "z": vector.z}
