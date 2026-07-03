from PySide6.QtCore import QPoint


def line_line(line1, line2):

    x1 = line1.start.x()
    y1 = line1.start.y()

    x2 = line1.end.x()
    y2 = line1.end.y()

    x3 = line2.start.x()
    y3 = line2.start.y()

    x4 = line2.end.x()
    y4 = line2.end.y()

    den = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)

    if abs(den) < 1e-9:
        return None

    px = (
        (x1*y2-y1*x2)*(x3-x4)
        -
        (x1-x2)*(x3*y4-y3*x4)
    ) / den

    py = (
        (x1*y2-y1*x2)*(y3-y4)
        -
        (y1-y2)*(x3*y4-y3*x4)
    ) / den

    if (
        min(x1, x2)-1 <= px <= max(x1, x2)+1 and
        min(y1, y2)-1 <= py <= max(y1, y2)+1 and
        min(x3, x4)-1 <= px <= max(x3, x4)+1 and
        min(y3, y4)-1 <= py <= max(y3, y4)+1
    ):
        return QPoint(int(px), int(py))

    return None