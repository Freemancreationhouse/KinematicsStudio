from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry.transforms import translate_point


def copy_entities(entity, dx, dy):
    """Return copied entities translated by a delta."""

    handler = _handler_for(entity)

    if handler is None:
        return []

    return handler(entity, dx, dy)


def preview_copy(entity, dx, dy):
    """Return preview entities for a copy operation."""

    return copy_entities(entity, dx, dy)


def copy(entity, dx, dy):
    """Backward-compatible helper returning the first copied entity."""

    copied = copy_entities(entity, dx, dy)

    if copied:
        return copied[0]

    return None


def _handler_for(entity):

    if _is_line(entity):
        return _copy_line

    if _is_rectangle(entity):
        return _copy_rectangle

    if _is_circle(entity):
        return _copy_circle

    return None


def _copy_line(entity, dx, dy):

    return [
        LineEntity(
            translate_point(entity.start, dx, dy),
            translate_point(entity.end, dx, dy)
        )
    ]


def _copy_rectangle(entity, dx, dy):

    return [
        RectangleEntity(
            translate_point(entity.p1, dx, dy),
            translate_point(entity.p2, dx, dy)
        )
    ]


def _copy_circle(entity, dx, dy):

    return [
        CircleEntity(
            translate_point(entity.center, dx, dy),
            entity.radius
        )
    ]


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")


def _is_circle(entity):

    return hasattr(entity, "center") and hasattr(entity, "radius")
