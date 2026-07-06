from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.geometry.primitives import is_degenerate_segment, rectangle_corners
from engine.geometry.transforms import mirror_point, unique_values


def mirror_entities(entity, line_start, line_end):
    """Return mirrored replacement entities for supported geometry."""

    if _line_degenerate(line_start, line_end):
        return None

    handler = _handler_for(entity)

    if handler is None:
        return None

    return handler(entity, line_start, line_end)


def preview_mirror(entity, line_start, line_end):
    """Return preview entities for a mirror operation."""

    return mirror_entities(entity, line_start, line_end)


def mirror(entity, line_start, line_end):
    """Backward-compatible helper returning the first mirrored entity."""

    replacements = mirror_entities(entity, line_start, line_end)

    if replacements:
        return replacements[0]

    return entity


def _handler_for(entity):

    if _is_line(entity):
        return _mirror_line

    if _is_rectangle(entity):
        return _mirror_rectangle

    if _is_circle(entity):
        return _mirror_circle

    if _is_polyline(entity):
        return _mirror_polyline

    return None


def _mirror_line(entity, line_start, line_end):

    return [
        LineEntity(
            mirror_point(entity.start, line_start, line_end),
            mirror_point(entity.end, line_start, line_end)
        )
    ]


def _mirror_rectangle(entity, line_start, line_end):

    mirrored = [
        mirror_point(point, line_start, line_end)
        for point in rectangle_corners(entity)
    ]

    rectangle = _axis_aligned_rectangle(mirrored)

    if rectangle:
        return [rectangle]

    return [
        LineEntity(start, end)
        for start, end in zip(mirrored, mirrored[1:] + mirrored[:1])
    ]


def _mirror_circle(entity, line_start, line_end):

    return [
        CircleEntity(
            mirror_point(entity.center, line_start, line_end),
            entity.radius
        )
    ]


def _mirror_polyline(entity, line_start, line_end):

    return None


def _axis_aligned_rectangle(points):

    xs = unique_values([point.x for point in points])
    ys = unique_values([point.y for point in points])

    if len(xs) != 2 or len(ys) != 2:
        return None

    return RectangleEntity(
        Vector2(min(xs), min(ys)),
        Vector2(max(xs), max(ys))
    )


def _line_degenerate(line_start, line_end):

    return is_degenerate_segment(line_start, line_end)


def _is_line(entity):

    return hasattr(entity, "start") and hasattr(entity, "end")


def _is_rectangle(entity):

    return hasattr(entity, "p1") and hasattr(entity, "p2")


def _is_circle(entity):

    return hasattr(entity, "center") and hasattr(entity, "radius")


def _is_polyline(entity):

    return hasattr(entity, "points")
