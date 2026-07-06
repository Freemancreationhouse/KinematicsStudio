from engine.entities import LineEntity
from engine.geometry.primitives import (
    point_to_segment_distance,
    rectangle_edges,
    segment_intersection,
)
from engine.geometry.tolerance import is_zero


def trim_entities(target, cutter, pick_point):
    """Return replacement entities after trimming target by cutter."""

    if _is_line(target):
        return _trim_line(target, cutter, pick_point)

    if _is_rectangle(target) and _is_line(cutter):
        return _trim_rectangle_edge(target, cutter, pick_point)

    return None


def preview_trim(target, cutter, pick_point):
    """Return preview entities for a possible trim operation."""

    return trim_entities(target, cutter, pick_point)


def _trim_line(target, cutter, pick_point):

    intersections = _line_cutter_intersections(target, cutter)

    if not intersections:
        return None

    point = min(intersections, key=lambda p: p.distance_to(pick_point))
    start_distance = pick_point.distance_to(target.start)
    end_distance = pick_point.distance_to(target.end)

    if start_distance <= end_distance:
        replacement = LineEntity(point.copy(), target.end.copy())
    else:
        replacement = LineEntity(target.start.copy(), point.copy())

    if is_zero(replacement.start.distance_to(replacement.end)):
        return None

    return [replacement]


def _trim_rectangle_edge(target, cutter, pick_point):

    edges = rectangle_edges(target)
    edge = min(edges, key=lambda item: point_to_segment_distance(pick_point, item[0], item[1]))
    point = segment_intersection(edge[0], edge[1], cutter.start, cutter.end)

    if point is None:
        return None

    replacements = []

    for start, end in edges:
        if start is edge[0] and end is edge[1]:
            replacement = _trim_edge_segment(start, end, point, pick_point)
            if replacement:
                replacements.append(replacement)
        else:
            replacements.append(LineEntity(start.copy(), end.copy()))

    return replacements


def _trim_edge_segment(start, end, point, pick_point):

    start_distance = pick_point.distance_to(start)
    end_distance = pick_point.distance_to(end)

    if start_distance <= end_distance:
        replacement = LineEntity(point.copy(), end.copy())
    else:
        replacement = LineEntity(start.copy(), point.copy())

    if is_zero(replacement.start.distance_to(replacement.end)):
        return None

    return replacement


def _line_cutter_intersections(target, cutter):

    if _is_line(cutter):
        point = segment_intersection(
            target.start,
            target.end,
            cutter.start,
            cutter.end
        )
        return [point] if point else []

    if _is_rectangle(cutter):
        points = []
        for start, end in rectangle_edges(cutter):
            point = segment_intersection(
                target.start,
                target.end,
                start,
                end
            )
            if point:
                points.append(point)
        return points

    return []

def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")
