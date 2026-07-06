from engine.entities import LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.geometry.primitives import rectangle_bounds, signed_distance_to_line
from engine.geometry.tolerance import is_zero, nearly_equal


def offset_entities(entity, point, distance=None):
    """Return offset entities for supported geometry."""

    handler = _handler_for(entity)

    if handler is None:
        return None

    return handler(entity, point, distance)


def preview_offset(entity, point, distance=None):
    """Return preview entities for an offset operation."""

    return offset_entities(entity, point, distance)


def offset(entity, point, distance=None):
    """Backward-compatible helper returning the first offset entity."""

    replacements = offset_entities(entity, point, distance)

    if replacements:
        return replacements[0]

    return entity


def _handler_for(entity):

    if _is_line(entity):
        return _offset_line

    if _is_rectangle(entity):
        return _offset_rectangle

    if _is_polyline(entity):
        return _offset_polyline

    if _is_circle(entity):
        return _offset_circle

    return None


def _offset_line(entity, point, distance):

    dx = entity.end.x - entity.start.x
    dy = entity.end.y - entity.start.y
    length = (dx * dx + dy * dy) ** 0.5

    if is_zero(length):
        return None

    normal = Vector2(-dy / length, dx / length)
    signed = signed_distance_to_line(entity.start, entity.end, point)
    amount = abs(distance) if distance is not None else abs(signed)

    if is_zero(amount):
        return None

    side = 1.0 if signed >= 0 else -1.0
    offset_vector = normal * (amount * side)

    return [
        LineEntity(
            entity.start + offset_vector,
            entity.end + offset_vector
        )
    ]


def _offset_rectangle(entity, point, distance):

    left, top, right, bottom = rectangle_bounds(entity)
    center = Vector2((left + right) * 0.5, (top + bottom) * 0.5)
    explicit = abs(distance) if distance is not None else None
    outward = _rectangle_outward(entity, point)
    amount = explicit if explicit is not None else _rectangle_offset_distance(entity, point)

    if is_zero(amount):
        return None

    if outward:
        left -= amount
        top -= amount
        right += amount
        bottom += amount
    else:
        left += amount
        top += amount
        right -= amount
        bottom -= amount

    if left >= right or top >= bottom:
        return None

    p1 = Vector2(left, top)
    p2 = Vector2(right, bottom)

    if (
        not nearly_equal((p1.x + p2.x) * 0.5, center.x) or
        not nearly_equal((p1.y + p2.y) * 0.5, center.y)
    ):
        return None

    return [RectangleEntity(p1, p2)]


def _offset_polyline(entity, point, distance):

    return None


def _offset_circle(entity, point, distance):

    return None


def _rectangle_offset_distance(entity, point):

    left, top, right, bottom = rectangle_bounds(entity)

    if left <= point.x <= right and top <= point.y <= bottom:
        return min(
            point.x - left,
            right - point.x,
            point.y - top,
            bottom - point.y
        )

    dx = max(left - point.x, 0.0, point.x - right)
    dy = max(top - point.y, 0.0, point.y - bottom)

    return max(dx, dy)


def _rectangle_outward(entity, point):

    left, top, right, bottom = rectangle_bounds(entity)

    return not (left < point.x < right and top < point.y < bottom)


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")


def _is_polyline(entity):

    return hasattr(entity, "points")


def _is_circle(entity):

    return hasattr(entity, "center") and hasattr(entity, "radius")
