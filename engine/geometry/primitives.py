from engine.geometry import Vector2
from engine.geometry.tolerance import GEOMETRY_EPSILON, is_zero, within


SEGMENT_DEGENERATE = "DEGENERATE"
SEGMENT_POINT = "POINT"
SEGMENT_LINE = "LINE"

ENDPOINT_START = "START"
ENDPOINT_END = "END"
ENDPOINT_INTERIOR = "INTERIOR"
ENDPOINT_OFF = "OFF"
ENDPOINT_DEGENERATE = "DEGENERATE"

INTERSECTION_DEGENERATE = "DEGENERATE"
INTERSECTION_PARALLEL = "PARALLEL"
INTERSECTION_COINCIDENT = "COINCIDENT"
INTERSECTION_OVERLAP = "OVERLAP"
INTERSECTION_TOUCH = "TOUCH"
INTERSECTION_CROSS = "CROSS"
INTERSECTION_DISJOINT = "DISJOINT"


def line_intersection(a1, a2, b1, b2, segment_a=True, segment_b=True):
    """Return (t, u, point) for line intersection, or None."""

    dax = a2.x - a1.x
    day = a2.y - a1.y
    dbx = b2.x - b1.x
    dby = b2.y - b1.y
    denominator = dax * dby - day * dbx

    if _is_parallel_delta(dax, day, dbx, dby):
        return None

    dx = b1.x - a1.x
    dy = b1.y - a1.y
    t = (dx * dby - dy * dbx) / denominator
    u = (dx * day - dy * dax) / denominator

    if segment_a and not within(t, 0.0, 1.0):
        return None

    if segment_b and not within(u, 0.0, 1.0):
        return None

    return t, u, Vector2(a1.x + t * dax, a1.y + t * day)


def segment_intersection(a1, a2, b1, b2):
    """Return segment intersection point, or None."""

    result = line_intersection(a1, a2, b1, b2)

    if result is None:
        return None

    return result[2]


def infinite_line_intersection(a1, a2, b1, b2):
    """Return (t, point) for infinite line intersection, or None."""

    result = line_intersection(a1, a2, b1, b2, False, False)

    if result is None:
        return None

    return result[0], result[2]


def infinite_segment_intersection(a1, a2, b1, b2):
    """Return (t, point) where first line is infinite and second is segment."""

    result = line_intersection(a1, a2, b1, b2, False, True)

    if result is None:
        return None

    return result[0], result[2]


def rectangle_corners(rect):
    """Return rectangle corners in drawing order."""

    x1 = rect.p1.x
    y1 = rect.p1.y
    x2 = rect.p2.x
    y2 = rect.p2.y

    return [
        Vector2(x1, y1),
        Vector2(x2, y1),
        Vector2(x2, y2),
        Vector2(x1, y2),
    ]


def rectangle_edges(rect):
    """Return rectangle edge point pairs in drawing order."""

    corners = rectangle_corners(rect)

    return list(zip(corners, corners[1:] + corners[:1]))


def rectangle_bounds(rect):
    """Return normalized rectangle bounds as left, top, right, bottom."""

    left = min(rect.p1.x, rect.p2.x)
    top = min(rect.p1.y, rect.p2.y)
    right = max(rect.p1.x, rect.p2.x)
    bottom = max(rect.p1.y, rect.p2.y)

    return left, top, right, bottom


def point_to_segment_distance(point, start, end):
    """Return shortest distance from a point to a segment."""

    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared <= GEOMETRY_EPSILON * GEOMETRY_EPSILON:
        return point.distance_to(start)

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    nearest = Vector2(start.x + t * dx, start.y + t * dy)

    return point.distance_to(nearest)


def signed_distance_to_line(start, end, point):
    """Return signed perpendicular distance from point to directed line."""

    dx = end.x - start.x
    dy = end.y - start.y
    length = (dx * dx + dy * dy) ** 0.5

    if is_zero(length):
        return 0.0

    return ((point.x - start.x) * (-dy) + (point.y - start.y) * dx) / length


def is_degenerate_segment(start, end):
    """Return True when segment length is within geometry tolerance."""

    return start.distance_to(end) <= GEOMETRY_EPSILON


def segment_classification(start, end):
    """Return the classification for a segment."""

    if is_degenerate_segment(start, end):
        return SEGMENT_DEGENERATE

    return SEGMENT_LINE


def endpoint_classification(point, start, end, epsilon=GEOMETRY_EPSILON):
    """Return where a point falls relative to a segment endpoint."""

    if is_degenerate_segment(start, end):
        if point.distance_to(start) <= epsilon:
            return ENDPOINT_DEGENERATE

        return ENDPOINT_OFF

    if point.distance_to(start) <= epsilon:
        return ENDPOINT_START

    if point.distance_to(end) <= epsilon:
        return ENDPOINT_END

    if point_to_segment_distance(point, start, end) <= epsilon:
        t = segment_parameter(point, start, end)

        if within(t, 0.0, 1.0, epsilon):
            return ENDPOINT_INTERIOR

    return ENDPOINT_OFF


def segment_parameter(point, start, end):
    """Return the parametric position of point on the segment line."""

    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared <= GEOMETRY_EPSILON * GEOMETRY_EPSILON:
        return 0.0

    return ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared


def are_parallel_segments(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return True when segment directions are parallel within tolerance."""

    dax = a2.x - a1.x
    day = a2.y - a1.y
    dbx = b2.x - b1.x
    dby = b2.y - b1.y

    return _is_parallel_delta(dax, day, dbx, dby, epsilon)


def are_collinear_segments(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return True when two segments lie on the same infinite line."""

    if is_degenerate_segment(a1, a2) or is_degenerate_segment(b1, b2):
        return False

    if not are_parallel_segments(a1, a2, b1, b2, epsilon):
        return False

    dax = a2.x - a1.x
    day = a2.y - a1.y
    offset_x = b1.x - a1.x
    offset_y = b1.y - a1.y
    cross = offset_x * day - offset_y * dax
    scale = max((dax * dax + day * day) ** 0.5, 1.0)

    return abs(cross) <= epsilon * scale


def overlapping_segment(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return the overlapping segment for collinear segments, or None."""

    if not are_collinear_segments(a1, a2, b1, b2, epsilon):
        return None

    axis = _dominant_axis(a1, a2)
    a_start = _axis_value(a1, axis)
    a_end = _axis_value(a2, axis)
    b_start = _axis_value(b1, axis)
    b_end = _axis_value(b2, axis)
    a_low, a_high = sorted((a_start, a_end))
    b_low, b_high = sorted((b_start, b_end))
    overlap_low = max(a_low, b_low)
    overlap_high = min(a_high, b_high)

    if overlap_high < overlap_low - epsilon:
        return None

    start = _point_at_axis_value(a1, a2, axis, overlap_low)
    end = _point_at_axis_value(a1, a2, axis, overlap_high)

    return start, end


def segments_overlap(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return True when two collinear segments overlap."""

    return overlapping_segment(a1, a2, b1, b2, epsilon) is not None


def intersection_classification(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return a structured classification for two segment intersections."""

    if is_degenerate_segment(a1, a2) or is_degenerate_segment(b1, b2):
        return _classification(INTERSECTION_DEGENERATE)

    result = line_intersection(a1, a2, b1, b2)

    if result is not None:
        t, u, point = result
        kind = _point_intersection_kind(t, u, epsilon)
        return _classification(kind, point=point, t=t, u=u)

    if are_collinear_segments(a1, a2, b1, b2, epsilon):
        overlap = overlapping_segment(a1, a2, b1, b2, epsilon)

        if overlap is None:
            return _classification(INTERSECTION_COINCIDENT)

        start, end = overlap

        if start.distance_to(end) <= epsilon:
            return _classification(INTERSECTION_TOUCH, point=start)

        return _classification(
            INTERSECTION_OVERLAP,
            segment=(start, end)
        )

    if are_parallel_segments(a1, a2, b1, b2, epsilon):
        return _classification(INTERSECTION_PARALLEL)

    return _classification(INTERSECTION_DISJOINT)


def classify_segment_intersection(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return the intersection type for two segments."""

    return intersection_classification(a1, a2, b1, b2, epsilon)["type"]


def shared_endpoint(a1, a2, b1, b2, epsilon=GEOMETRY_EPSILON):
    """Return a shared endpoint point when two segments touch at endpoints."""

    for point in (a1, a2):
        for other in (b1, b2):
            if point.distance_to(other) <= epsilon:
                return point.copy()

    return None


def _classification(kind, point=None, segment=None, t=None, u=None):

    return {
        "type": kind,
        "point": point,
        "segment": segment,
        "t": t,
        "u": u,
    }


def _point_intersection_kind(t, u, epsilon):

    on_endpoint = (
        abs(t) <= epsilon or
        abs(t - 1.0) <= epsilon or
        abs(u) <= epsilon or
        abs(u - 1.0) <= epsilon
    )

    if on_endpoint:
        return INTERSECTION_TOUCH

    return INTERSECTION_CROSS


def _is_parallel_delta(dax, day, dbx, dby, epsilon=GEOMETRY_EPSILON):

    denominator = dax * dby - day * dbx
    a_length = (dax * dax + day * day) ** 0.5
    b_length = (dbx * dbx + dby * dby) ** 0.5
    scale = a_length * b_length

    if scale <= epsilon * epsilon:
        return True

    return abs(denominator) <= epsilon * scale


def _dominant_axis(start, end):

    if abs(end.x - start.x) >= abs(end.y - start.y):
        return "x"

    return "y"


def _axis_value(point, axis):

    return point.x if axis == "x" else point.y


def _point_at_axis_value(start, end, axis, value):

    start_value = _axis_value(start, axis)
    end_value = _axis_value(end, axis)
    denominator = end_value - start_value

    if is_zero(denominator):
        return start.copy()

    t = (value - start_value) / denominator

    return Vector2(
        start.x + (end.x - start.x) * t,
        start.y + (end.y - start.y) * t
    )
