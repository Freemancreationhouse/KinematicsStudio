from engine.geometry.bounding_box import BoundingBox
from engine.geometry.vector2 import Vector2
from engine.geometry.primitives import point_to_segment_distance
from engine.geometry.tolerance import GEOMETRY_EPSILON


def clone_points(points):
    """Return independent copies of curve points."""

    return [point.copy() for point in points or []]


def curve_bounds(points):
    """Return a bounding box for a point sequence."""

    box = BoundingBox()

    for point in points or []:
        box.add(point)

    return box


def polyline_segments(points, closed=False):
    """Return drawable segment pairs for a polyline-like curve."""

    vertices = list(points or [])

    if len(vertices) < 2:
        return []

    segments = list(zip(vertices, vertices[1:]))

    if closed and len(vertices) > 2:
        segments.append((vertices[-1], vertices[0]))

    return segments


def curve_length(points, closed=False):
    """Return total length of curve segment pairs."""

    return sum(
        start.distance_to(end)
        for start, end in polyline_segments(points, closed)
    )


def nearest_on_curve(point, points, closed=False):
    """Return nearest point on a polyline-like curve."""

    nearest = None
    best = float("inf")

    for start, end in polyline_segments(points, closed):
        candidate = nearest_on_segment(point, start, end)
        distance = point.distance_to(candidate)

        if distance < best:
            best = distance
            nearest = candidate

    return nearest


def nearest_on_segment(point, start, end):
    """Return nearest point on one segment."""

    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared <= GEOMETRY_EPSILON * GEOMETRY_EPSILON:
        return start.copy()

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    t = max(0.0, min(1.0, t))

    return Vector2(start.x + dx * t, start.y + dy * t)


def hit_curve(point, points, closed=False, tolerance=5.0):
    """Return True when a point is near a curve segment."""

    return any(
        point_to_segment_distance(point, start, end) <= tolerance
        for start, end in polyline_segments(points, closed)
    )


def midpoint(start, end):
    """Return the midpoint between two points."""

    return Vector2((start.x + end.x) * 0.5, (start.y + end.y) * 0.5)


def catmull_rom_points(control_points, samples_per_segment=16):
    """Interpolate control points with a Catmull-Rom spline."""

    points = list(control_points or [])

    if len(points) < 2:
        return clone_points(points)

    if len(points) == 2:
        return clone_points(points)

    samples = []

    for index in range(len(points) - 1):
        p0 = points[max(index - 1, 0)]
        p1 = points[index]
        p2 = points[index + 1]
        p3 = points[min(index + 2, len(points) - 1)]

        for step in range(samples_per_segment):
            t = step / float(samples_per_segment)
            samples.append(_catmull_rom_point(p0, p1, p2, p3, t))

    samples.append(points[-1].copy())

    return samples


def _catmull_rom_point(p0, p1, p2, p3, t):

    t2 = t * t
    t3 = t2 * t

    return Vector2(
        0.5 * (
            (2.0 * p1.x) +
            (-p0.x + p2.x) * t +
            (2.0 * p0.x - 5.0 * p1.x + 4.0 * p2.x - p3.x) * t2 +
            (-p0.x + 3.0 * p1.x - 3.0 * p2.x + p3.x) * t3
        ),
        0.5 * (
            (2.0 * p1.y) +
            (-p0.y + p2.y) * t +
            (2.0 * p0.y - 5.0 * p1.y + 4.0 * p2.y - p3.y) * t2 +
            (-p0.y + 3.0 * p1.y - 3.0 * p2.y + p3.y) * t3
        ),
    )
