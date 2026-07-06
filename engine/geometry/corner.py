from engine.geometry.primitives import (
    INTERSECTION_PARALLEL,
    INTERSECTION_OVERLAP,
    INTERSECTION_COINCIDENT,
    intersection_classification,
    infinite_line_intersection,
    point_to_segment_distance,
)
from engine.geometry.tolerance import GEOMETRY_EPSILON, is_zero


def line_line_corner(line_a, line_b, pick_a=None, pick_b=None):
    """Return reusable line-line corner data for modify operations."""

    classification = intersection_classification(
        line_a.start,
        line_a.end,
        line_b.start,
        line_b.end
    )

    if classification["type"] in (
        INTERSECTION_PARALLEL,
        INTERSECTION_OVERLAP,
        INTERSECTION_COINCIDENT,
    ):
        return None

    result = infinite_line_intersection(
        line_a.start,
        line_a.end,
        line_b.start,
        line_b.end
    )

    if result is None:
        return None

    _, vertex = result
    side_a = selected_line_side(line_a, vertex, pick_a)
    side_b = selected_line_side(line_b, vertex, pick_b)

    if side_a is None or side_b is None:
        return None

    return {
        "vertex": vertex,
        "line_a": line_a,
        "line_b": line_b,
        "side_a": side_a,
        "side_b": side_b,
        "classification": classification,
    }


def selected_line_side(line, vertex, pick_point=None):
    """Return endpoint, direction and available length for one line side."""

    start_distance = line.start.distance_to(vertex)
    end_distance = line.end.distance_to(vertex)

    if pick_point is not None:
        start_pick = point_to_segment_distance(pick_point, vertex, line.start)
        end_pick = point_to_segment_distance(pick_point, vertex, line.end)
        endpoint = line.start if start_pick <= end_pick else line.end
    else:
        endpoint = line.start if start_distance >= end_distance else line.end

    length = endpoint.distance_to(vertex)

    if length <= GEOMETRY_EPSILON:
        return None

    return {
        "endpoint": endpoint.copy(),
        "direction": unit_direction(vertex, endpoint),
        "length": length,
    }


def unit_direction(start, end):
    """Return a unit vector from start to end."""

    dx = end.x - start.x
    dy = end.y - start.y
    length = (dx * dx + dy * dy) ** 0.5

    if is_zero(length):
        return None

    from engine.geometry import Vector2

    return Vector2(dx / length, dy / length)


def point_from(vertex, direction, distance):
    """Return a point from vertex along direction by distance."""

    from engine.geometry import Vector2

    return Vector2(
        vertex.x + direction.x * distance,
        vertex.y + direction.y * distance
    )


def dot(a, b):
    """Return dot product for two vectors."""

    return a.x * b.x + a.y * b.y


def cross(a, b):
    """Return 2D cross product for two vectors."""

    return a.x * b.y - a.y * b.x
