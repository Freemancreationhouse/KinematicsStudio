from math import sqrt

from PySide6.QtCore import QPoint

from engine.entities.line import Line


def offset(entity, distance):

    if not hasattr(entity, "start"):
        return None

    x1 = entity.start.x()
    y1 = entity.start.y()

    x2 = entity.end.x()
    y2 = entity.end.y()

    dx = x2 - x1
    dy = y2 - y1

    length = sqrt(dx * dx + dy * dy)

    if length == 0:
        return None

    nx = -dy / length
    ny = dx / length

    ox = nx * distance
    oy = ny * distance

    p1 = QPoint(
        int(x1 + ox),
        int(y1 + oy)
    )

    p2 = QPoint(
        int(x2 + ox),
        int(y2 + oy)
    )

    return Line(
        p1,
        p2
    )