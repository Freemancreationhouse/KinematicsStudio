from engine.entities import LineEntity
from engine.geometry.primitives import (
    infinite_line_intersection,
    infinite_segment_intersection,
    point_to_segment_distance,
    rectangle_edges,
)
from engine.geometry.tolerance import is_zero


def extend_entities(target, boundary, pick_point):
    """Return replacement entities after extending target to boundary."""

    if _is_line(target):
        return _extend_line(target, boundary, pick_point)

    if _is_rectangle(target) and _is_line(boundary):
        return _extend_rectangle_edge(target, boundary, pick_point)

    return None


def preview_extend(target, boundary, pick_point):
    """Return preview entities for a possible extend operation."""

    return extend_entities(target, boundary, pick_point)


def extend(line, boundary):
    """Backward-compatible helper returning an extended line when possible."""

    replacements = extend_entities(line, boundary, line.end)

    if replacements and len(replacements) == 1:
        return replacements[0]

    return line


def _extend_line(target, boundary, pick_point):

    intersections = _line_boundary_intersections(target, boundary)

    if not intersections:
        return None

    chosen = _best_line_extension(target, intersections, pick_point)

    if chosen is None:
        return None

    t, point = chosen

    if t < 0:
        replacement = LineEntity(point.copy(), target.end.copy())
    else:
        replacement = LineEntity(target.start.copy(), point.copy())

    if is_zero(replacement.start.distance_to(replacement.end)):
        return None

    return [replacement]


def _extend_rectangle_edge(target, boundary, pick_point):

    edges = rectangle_edges(target)
    edge = min(edges, key=lambda item: point_to_segment_distance(pick_point, item[0], item[1]))
    intersections = _edge_boundary_intersections(edge[0], edge[1], boundary)

    if not intersections:
        return None

    chosen = _best_segment_extension(edge[0], edge[1], intersections, pick_point)

    if chosen is None:
        return None

    t, point = chosen
    replacements = []

    for start, end in edges:
        if start is edge[0] and end is edge[1]:
            if t < 0:
                replacements.append(LineEntity(point.copy(), end.copy()))
            else:
                replacements.append(LineEntity(start.copy(), point.copy()))
        else:
            replacements.append(LineEntity(start.copy(), end.copy()))

    return replacements


def _line_boundary_intersections(target, boundary):

    if _is_line(boundary):
        result = infinite_line_intersection(
            target.start,
            target.end,
            boundary.start,
            boundary.end
        )

        return [result] if result else []

    if _is_rectangle(boundary):
        intersections = []
        for start, end in rectangle_edges(boundary):
            result = infinite_segment_intersection(
                target.start,
                target.end,
                start,
                end
            )
            if result:
                intersections.append(result)
        return intersections

    return []


def _edge_boundary_intersections(start, end, boundary):

    if not _is_line(boundary):
        return []

    result = infinite_line_intersection(
        start,
        end,
        boundary.start,
        boundary.end
    )

    return [result] if result else []


def _best_line_extension(target, intersections, pick_point):

    return _best_segment_extension(target.start, target.end, intersections, pick_point)


def _best_segment_extension(start, end, intersections, pick_point):

    start_pick = pick_point.distance_to(start)
    end_pick = pick_point.distance_to(end)
    prefer_start = start_pick <= end_pick
    candidates = []

    for t, point in intersections:
        if prefer_start and t < 0:
            candidates.append((abs(t), t, point))
        elif not prefer_start and t > 1:
            candidates.append((abs(t - 1), t, point))

    if not candidates:
        return None

    _, t, point = min(candidates, key=lambda item: item[0])

    return t, point

def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")
