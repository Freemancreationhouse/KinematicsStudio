from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.geometry import Vector3

from engine.gizmo.gizmo_handles import GizmoHandleKind
from engine.gizmo.gizmo_state import GizmoState


@dataclass(frozen=True)
class GizmoPickResult:
    """Result of picking a transform gizmo handle."""

    handle_id: str
    distance: float
    valid: bool = True


class GizmoPicker:
    """Screen and ray picking helper for gizmo handles."""

    def pick(
        self,
        state: GizmoState,
        ray: Any,
        *,
        tolerance: float = 14.0,
    ) -> GizmoPickResult | None:
        """Return the nearest picked handle for a ray."""

        best: GizmoPickResult | None = None
        origin = state.origin
        size = float(state.metadata.get("screen_size", 120.0))
        for handle in state.handles.values():
            if not handle.enabled or not handle.visible:
                continue
            distance = self._distance_to_handle(ray, origin, handle, size)
            if distance > tolerance:
                continue
            if best is None or distance < best.distance:
                best = GizmoPickResult(handle.handle_id, distance)
        state.set_hovered(best.handle_id if best else "")
        return best

    def _distance_to_handle(
        self,
        ray: Any,
        origin: Vector3,
        handle: Any,
        size: float,
    ) -> float:
        """Return approximate ray distance to a handle."""

        if handle.kind in {
            GizmoHandleKind.MOVE_CENTER,
            GizmoHandleKind.SCALE_UNIFORM,
        }:
            return _ray_point_distance(ray, origin)
        if handle.direction.length_squared() > 0.0:
            return _ray_segment_distance(ray, origin, origin + handle.direction * size)
        return _ray_point_distance(ray, origin)


def _ray_point_distance(ray: Any, point: Vector3) -> float:
    """Return approximate distance from ray to point."""

    direction = getattr(ray, "direction", Vector3(1.0, 0.0, 0.0))
    origin = getattr(ray, "origin", Vector3())
    between = point - origin
    denominator = direction.dot(direction)
    distance = 0.0 if denominator == 0.0 else max(0.0, between.dot(direction) / denominator)
    closest = ray.point_at(distance) if hasattr(ray, "point_at") else origin + direction * distance
    return closest.distance_to(point)


def _ray_segment_distance(ray: Any, start: Vector3, end: Vector3) -> float:
    """Return approximate distance between a ray and a segment."""

    direction = getattr(ray, "direction", Vector3(1.0, 0.0, 0.0))
    ray_origin = getattr(ray, "origin", Vector3())
    segment = end - start
    between = ray_origin - start
    a = direction.dot(direction)
    b = direction.dot(segment)
    c = segment.dot(segment)
    d = direction.dot(between)
    e = segment.dot(between)
    denominator = a * c - b * b
    if abs(denominator) < 1e-9:
        ray_t = 0.0
        segment_t = 0.0
    else:
        ray_t = max(0.0, (b * e - c * d) / denominator)
        segment_t = max(0.0, min(1.0, (a * e - b * d) / denominator))
    ray_point = ray.point_at(ray_t) if hasattr(ray, "point_at") else ray_origin + direction * ray_t
    segment_point = start + segment * segment_t
    return ray_point.distance_to(segment_point)
