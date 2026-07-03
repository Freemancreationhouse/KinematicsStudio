from engine.entities.line import Line
from engine.geometry.intersection import line_line


def trim(line, cutter):

    p = line_line(line, cutter)

    if p is None:
        return None

    d1 = (
        (line.start.x()-p.x())**2 +
        (line.start.y()-p.y())**2
    )

    d2 = (
        (line.end.x()-p.x())**2 +
        (line.end.y()-p.y())**2
    )

    if d1 > d2:

        return Line(
            line.start,
            p
        )

    return Line(
        p,
        line.end
    )