from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry.primitives import rectangle_corners
from engine.geometry.tolerance import is_zero
from engine.geometry.transforms import scale_point


def scale_entities(entity, base_point, factor):
    """Return scaled replacement entities for supported geometry."""

    if is_zero(factor):
        return None

    handler = _handler_for(entity)

    if handler is None:
        return None

    return handler(entity, base_point, factor)


def preview_scale(entity, base_point, factor):
    """Return preview entities for a scale operation."""

    return scale_entities(entity, base_point, factor)


def scale(entity, base_point, factor):
    """Backward-compatible helper returning the first scaled entity."""

    replacements = scale_entities(entity, base_point, factor)

    if replacements:
        return replacements[0]

    return entity


def _handler_for(entity):

    if _is_line(entity):
        return _scale_line

    if _is_rectangle(entity):
        return _scale_rectangle

    if _is_circle(entity):
        return _scale_circle

    if _is_polyline(entity):
        return _scale_polyline

    return None


def _scale_line(entity, base_point, factor):

    return [
        LineEntity(
            scale_point(entity.start, base_point, factor),
            scale_point(entity.end, base_point, factor)
        )
    ]


def _scale_rectangle(entity, base_point, factor):

    corners = [
        scale_point(point, base_point, factor)
        for point in rectangle_corners(entity)
    ]

    return [
        RectangleEntity(corners[0], corners[2])
    ]


def _scale_circle(entity, base_point, factor):

    return [
        CircleEntity(
            scale_point(entity.center, base_point, factor),
            abs(entity.radius * factor)
        )
    ]


def _scale_polyline(entity, base_point, factor):

    return None


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")


def _is_circle(entity):

    return hasattr(entity, "center") and hasattr(entity, "radius")


def _is_polyline(entity):

    return hasattr(entity, "points")
