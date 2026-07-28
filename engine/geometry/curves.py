from math import atan2, cos, degrees, pi, radians, sin, sqrt

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


def angle_degrees(center, point):
    """Return the mathematical angle from center to point in degrees."""

    return degrees(atan2(point.y - center.y, point.x - center.x))


def normalize_angle(angle):
    """Return an angle normalized into the [0, 360) range."""

    value = float(angle) % 360.0

    return value + 360.0 if value < 0.0 else value


def counter_clockwise_span(start_angle, end_angle):
    """Return the positive counter-clockwise span from start to end."""

    return (normalize_angle(end_angle) - normalize_angle(start_angle)) % 360.0


def clockwise_span(start_angle, end_angle):
    """Return the negative clockwise span from start to end."""

    span = counter_clockwise_span(start_angle, end_angle)

    return span - 360.0 if span else 0.0


def shortest_arc_span(start_angle, end_angle):
    """Return the shortest signed span from start to end."""

    span = counter_clockwise_span(start_angle, end_angle)

    return span - 360.0 if span > 180.0 else span


def arc_points(center, radius, start_angle, end_angle, clockwise=False, segments=64):
    """Return sampled points along an arc."""

    radius = float(radius)

    if radius <= GEOMETRY_EPSILON:
        return [center.copy()]

    span = clockwise_span(start_angle, end_angle) if clockwise else counter_clockwise_span(start_angle, end_angle)

    if abs(span) <= GEOMETRY_EPSILON:
        span = -360.0 if clockwise else 360.0

    count = max(2, int(abs(span) / 360.0 * max(segments, 8)) + 1)

    return [
        point_on_circle(center, radius, start_angle + span * index / (count - 1))
        for index in range(count)
    ]


def point_on_circle(center, radius, angle):
    """Return a point on a circle."""

    theta = radians(angle)

    return Vector2(center.x + cos(theta) * radius, center.y + sin(theta) * radius)


def point_on_ellipse(center, radius_x, radius_y, rotation, angle):
    """Return a point on a rotated ellipse."""

    theta = radians(angle)
    rotate = radians(rotation)
    local_x = cos(theta) * radius_x
    local_y = sin(theta) * radius_y
    c = cos(rotate)
    s = sin(rotate)

    return Vector2(
        center.x + local_x * c - local_y * s,
        center.y + local_x * s + local_y * c,
    )


def ellipse_points(center, radius_x, radius_y, rotation=0.0, segments=96):
    """Return sampled points along a rotated ellipse."""

    radius_x = abs(float(radius_x))
    radius_y = abs(float(radius_y))

    if radius_x <= GEOMETRY_EPSILON or radius_y <= GEOMETRY_EPSILON:
        return [center.copy()]

    return [
        point_on_ellipse(center, radius_x, radius_y, rotation, 360.0 * index / segments)
        for index in range(segments)
    ]


def regular_polygon_points(center, radius, sides, rotation=0.0):
    """Return vertices for a regular polygon."""

    sides = max(3, min(360, int(sides)))
    radius = abs(float(radius))

    if radius <= GEOMETRY_EPSILON:
        return [center.copy() for _index in range(sides)]

    return [
        point_on_circle(center, radius, rotation + 360.0 * index / sides)
        for index in range(sides)
    ]


def polygon_area(points):
    """Return the absolute area of a polygon point loop."""

    vertices = list(points or [])

    if len(vertices) < 3:
        return 0.0

    area = 0.0

    for start, end in zip(vertices, vertices[1:] + vertices[:1]):
        area += start.x * end.y - end.x * start.y

    return abs(area) * 0.5


def polygon_perimeter(points):
    """Return the perimeter of a polygon point loop."""

    return curve_length(points, True)


def ellipse_perimeter(radius_x, radius_y):
    """Return Ramanujan's approximation of ellipse perimeter."""

    a = abs(float(radius_x))
    b = abs(float(radius_y))

    if a <= GEOMETRY_EPSILON or b <= GEOMETRY_EPSILON:
        return 0.0

    h = ((a - b) ** 2) / ((a + b) ** 2)

    return pi * (a + b) * (1.0 + (3.0 * h) / (10.0 + sqrt(4.0 - 3.0 * h)))


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
