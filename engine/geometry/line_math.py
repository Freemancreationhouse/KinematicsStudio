from math import sqrt


def length(line):

    return sqrt(

        (line.end.x()-line.start.x())**2 +

        (line.end.y()-line.start.y())**2

    )


def midpoint(line):

    return line.start.__class__(

        (line.start.x()+line.end.x())//2,

        (line.start.y()+line.end.y())//2

    )


def distance(p1, p2):

    return sqrt(

        (p1.x()-p2.x())**2 +

        (p1.y()-p2.y())**2

    )