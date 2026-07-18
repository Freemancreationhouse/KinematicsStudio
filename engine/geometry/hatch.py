from engine.geometry import BoundingBox, Vector2
from engine.geometry.primitives import rectangle_corners
from engine.geometry.tolerance import GEOMETRY_EPSILON


def boundary_points_from_entity(entity):
    """Return closed boundary points for a supported boundary entity."""

    if hasattr(entity, "p1") and hasattr(entity, "p2"):
        return rectangle_corners(entity)

    if hasattr(entity, "points") and (
        getattr(entity, "closed", False) or
        (
            entity.points and
            entity.points[0].distance_to(entity.points[-1]) <= GEOMETRY_EPSILON
        )
    ):
        return closed_boundary_points(entity.points)

    return []


def closed_boundary_points(points):
    """Return polygon points when a point sequence forms a closed boundary."""

    if not points or len(points) < 3:
        return []

    result = [point.copy() for point in points]

    if result[0].distance_to(result[-1]) <= GEOMETRY_EPSILON:
        result.pop()

    if len(result) < 3:
        return []

    return result


def is_closed_boundary(entity):
    """Return True when the entity can provide a closed hatch boundary."""

    return len(boundary_points_from_entity(entity)) >= 3


def polygon_bounds(points):
    """Return a bounding box for polygon points."""

    box = BoundingBox()

    for point in points:
        box.add(point)

    return box


def polygon_area(points):
    """Return signed polygon area."""

    if len(points) < 3:
        return 0.0

    total = 0.0

    for index, point in enumerate(points):
        other = points[(index + 1) % len(points)]
        total += point.x * other.y - other.x * point.y

    return total * 0.5


def point_in_polygon(point, points):
    """Return True when point lies inside a closed polygon."""

    if len(points) < 3:
        return False

    inside = False
    j = len(points) - 1

    for i, current in enumerate(points):
        previous = points[j]

        if (
            (current.y > point.y) != (previous.y > point.y) and
            point.x < (
                (previous.x - current.x) *
                (point.y - current.y) /
                ((previous.y - current.y) or GEOMETRY_EPSILON) +
                current.x
            )
        ):
            inside = not inside

        j = i

    return inside


def polygon_segments(points):
    """Return edge segments for closed polygon points."""

    if len(points) < 2:
        return []

    return list(zip(points, points[1:] + points[:1]))
