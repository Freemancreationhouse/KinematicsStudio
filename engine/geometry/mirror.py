from PySide6.QtCore import QPoint

from engine.entities.line import Line


def mirror(entity):

    if not hasattr(entity, "start"):
        return None

    p1 = QPoint(
        -entity.start.x(),
        entity.start.y()
    )

    p2 = QPoint(
        -entity.end.x(),
        entity.end.y()
    )

    return Line(p1, p2)