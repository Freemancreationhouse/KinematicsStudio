from engine.entities import CircleEntity, LineEntity
from engine.geometry.primitives import rectangle_corners
from engine.geometry.transforms import rotate_point


def rotate_entities(entity, base_point, angle_degrees):
    """Return rotated replacement entities for supported geometry."""

    handler = _handler_for(entity)

    if handler is None:
        return None

    return handler(entity, base_point, angle_degrees)


def preview_rotate(entity, base_point, angle_degrees):
    """Return preview entities for a rotation operation."""

    return rotate_entities(entity, base_point, angle_degrees)


def rotate(entity, base_point, angle_degrees):
    """Backward-compatible helper returning the first rotated entity."""

    replacements = rotate_entities(entity, base_point, angle_degrees)

    if replacements:
        return replacements[0]

    return entity


def _handler_for(entity):

    if _is_line(entity):
        return _rotate_line

    if _is_rectangle(entity):
        return _rotate_rectangle

    if _is_circle(entity):
        return _rotate_circle

    if _is_polyline(entity):
        return _rotate_polyline

    return None


def _rotate_line(entity, base_point, angle_degrees):

    return [
        LineEntity(
            rotate_point(entity.start, base_point, angle_degrees),
            rotate_point(entity.end, base_point, angle_degrees)
        )
    ]


def _rotate_rectangle(entity, base_point, angle_degrees):

    corners = rectangle_corners(entity)
    rotated = [
        rotate_point(point, base_point, angle_degrees)
        for point in corners
    ]

    return [
        LineEntity(start, end)
        for start, end in zip(rotated, rotated[1:] + rotated[:1])
    ]


def _rotate_circle(entity, base_point, angle_degrees):

    return [
        CircleEntity(
            rotate_point(entity.center, base_point, angle_degrees),
            entity.radius
        )
    ]


def _rotate_polyline(entity, base_point, angle_degrees):

    return None


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")


def _is_circle(entity):

    return hasattr(entity, "center") and hasattr(entity, "radius")


def _is_polyline(entity):

    return hasattr(entity, "points")
