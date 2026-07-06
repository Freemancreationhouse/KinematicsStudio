from engine.entities import LineEntity
from engine.geometry.corner import line_line_corner, point_from
from engine.geometry.tolerance import GEOMETRY_EPSILON, is_zero


def chamfer_entities(entity_a, entity_b, distance, pick_a=None, pick_b=None):
    """Return line-line chamfer replacements for supported geometry."""

    if not (_is_line(entity_a) and _is_line(entity_b)):
        return None

    distance = abs(float(distance))

    if is_zero(distance):
        return None

    corner = line_line_corner(entity_a, entity_b, pick_a, pick_b)

    if corner is None:
        return None

    side_a = corner["side_a"]
    side_b = corner["side_b"]

    if (
        distance >= side_a["length"] - GEOMETRY_EPSILON or
        distance >= side_b["length"] - GEOMETRY_EPSILON
    ):
        return None

    vertex = corner["vertex"]
    point_a = point_from(vertex, side_a["direction"], distance)
    point_b = point_from(vertex, side_b["direction"], distance)

    return [
        LineEntity(point_a, side_a["endpoint"].copy()),
        LineEntity(point_b, side_b["endpoint"].copy()),
        LineEntity(point_a.copy(), point_b.copy()),
    ]


def preview_chamfer(entity_a, entity_b, distance, pick_a=None, pick_b=None):
    """Return preview entities for a chamfer operation."""

    return chamfer_entities(entity_a, entity_b, distance, pick_a, pick_b)


def chamfer(entity_a, entity_b, distance):
    """Backward-compatible helper returning chamfer entities."""

    return chamfer_entities(entity_a, entity_b, distance)


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")
