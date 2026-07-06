from math import acos, atan2, degrees, pi, sin, tan

from engine.entities import ArcEntity, LineEntity
from engine.geometry.corner import dot, line_line_corner, point_from
from engine.geometry.tolerance import GEOMETRY_EPSILON, is_zero


def fillet_entities(entity_a, entity_b, radius, pick_a=None, pick_b=None):
    """Return line-line fillet replacements for supported geometry."""

    if not (_is_line(entity_a) and _is_line(entity_b)):
        return None

    radius = abs(float(radius))

    if is_zero(radius):
        return None

    corner = line_line_corner(entity_a, entity_b, pick_a, pick_b)

    if corner is None:
        return None

    side_a = corner["side_a"]
    side_b = corner["side_b"]
    angle = _corner_angle(side_a["direction"], side_b["direction"])

    if angle is None:
        return None

    tangent_distance = radius / tan(angle * 0.5)

    if (
        tangent_distance <= GEOMETRY_EPSILON or
        tangent_distance >= side_a["length"] - GEOMETRY_EPSILON or
        tangent_distance >= side_b["length"] - GEOMETRY_EPSILON
    ):
        return None

    vertex = corner["vertex"]
    tangent_a = point_from(vertex, side_a["direction"], tangent_distance)
    tangent_b = point_from(vertex, side_b["direction"], tangent_distance)
    center = _fillet_center(vertex, side_a["direction"], side_b["direction"], radius, angle)

    if center is None:
        return None

    arc = ArcEntity(
        center,
        radius,
        _angle(center, tangent_a),
        _angle(center, tangent_b)
    )

    return [
        LineEntity(tangent_a, side_a["endpoint"].copy()),
        LineEntity(tangent_b, side_b["endpoint"].copy()),
        arc,
    ]


def preview_fillet(entity_a, entity_b, radius, pick_a=None, pick_b=None):
    """Return preview entities for a fillet operation."""

    return fillet_entities(entity_a, entity_b, radius, pick_a, pick_b)


def fillet(entity_a, entity_b, radius):
    """Backward-compatible helper returning fillet entities."""

    return fillet_entities(entity_a, entity_b, radius)


def _corner_angle(direction_a, direction_b):

    value = max(-1.0, min(1.0, dot(direction_a, direction_b)))
    angle = acos(value)

    if is_zero(angle) or is_zero(abs(angle - pi)):
        return None

    return angle


def _fillet_center(vertex, direction_a, direction_b, radius, angle):

    from engine.geometry import Vector2

    bisector = Vector2(
        direction_a.x + direction_b.x,
        direction_a.y + direction_b.y
    )
    length = (bisector.x * bisector.x + bisector.y * bisector.y) ** 0.5

    if is_zero(length):
        return None

    distance = radius / sin(angle * 0.5)

    return Vector2(
        vertex.x + bisector.x / length * distance,
        vertex.y + bisector.y / length * distance
    )


def _angle(center, point):

    return degrees(atan2(point.y - center.y, point.x - center.x))


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")
