from math import cos, radians, sin

from engine.geometry import Vector2
from engine.geometry.primitives import is_degenerate_segment
from engine.geometry.tolerance import GEOMETRY_EPSILON


def rotate_point(point, base_point, angle_degrees):
    """Return a point rotated around a base point by degrees."""

    angle = radians(angle_degrees)
    c = cos(angle)
    s = sin(angle)
    dx = point.x - base_point.x
    dy = point.y - base_point.y

    return Vector2(
        base_point.x + dx * c - dy * s,
        base_point.y + dx * s + dy * c
    )


def scale_point(point, base_point, factor):
    """Return a point scaled from a base point by a factor."""

    return Vector2(
        base_point.x + (point.x - base_point.x) * factor,
        base_point.y + (point.y - base_point.y) * factor
    )


def translate_point(point, dx, dy):
    """Return a point translated by a delta."""

    return Vector2(point.x + dx, point.y + dy)


def scale_factor_from_points(base_point, reference_point, current_point):
    """Return scale factor from base/reference/current points."""

    reference_distance = base_point.distance_to(reference_point)
    current_distance = base_point.distance_to(current_point)

    if reference_distance <= GEOMETRY_EPSILON:
        return 1.0

    return current_distance / reference_distance


def mirror_point(point, line_start, line_end):
    """Return a point mirrored across an infinite line."""

    dx = line_end.x - line_start.x
    dy = line_end.y - line_start.y
    length_squared = dx * dx + dy * dy

    if is_degenerate_segment(line_start, line_end):
        return point.copy()

    t = (
        (point.x - line_start.x) * dx +
        (point.y - line_start.y) * dy
    ) / length_squared
    projection = Vector2(
        line_start.x + t * dx,
        line_start.y + t * dy
    )

    return Vector2(
        projection.x * 2.0 - point.x,
        projection.y * 2.0 - point.y
    )


def unique_values(values, epsilon=GEOMETRY_EPSILON):
    """Return scalar values unique within geometry tolerance."""

    unique = []

    for value in values:
        if not any(abs(value - existing) <= epsilon for existing in unique):
            unique.append(value)

    return unique
