from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPen


class Rectangle:

    def __init__(self, p1, p2):

        self.p1 = p1
        self.p2 = p2

        self.selected = False

    # -------------------------------------------------

    def _x(self, p):

        return p.x() if callable(getattr(p, "x", None)) else p.x

    def _y(self, p):

        return p.y() if callable(getattr(p, "y", None)) else p.y

    def _set(self, p, x, y):

        if callable(getattr(p, "setX", None)):

            p.setX(int(x))
            p.setY(int(y))

        else:

            p.x = x
            p.y = y

    # -------------------------------------------------

    def draw(self, painter):

        if self.selected:
            painter.setPen(QPen(QColor("#FFFF00"), 3))
        else:
            painter.setPen(QPen(QColor("#00FF66"), 2))

        x = min(self._x(self.p1), self._x(self.p2))
        y = min(self._y(self.p1), self._y(self.p2))

        w = abs(self._x(self.p2) - self._x(self.p1))
        h = abs(self._y(self.p2) - self._y(self.p1))

        painter.drawRect(

            int(x),
            int(y),
            int(w),
            int(h)

        )

    # -------------------------------------------------

    def hit_test(self, p):

        px = p.x()
        py = p.y()

        x1 = min(self._x(self.p1), self._x(self.p2))
        y1 = min(self._y(self.p1), self._y(self.p2))

        x2 = max(self._x(self.p1), self._x(self.p2))
        y2 = max(self._y(self.p1), self._y(self.p2))

        tol = 6

        if abs(px - x1) <= tol and y1 - tol <= py <= y2 + tol:
            return True

        if abs(px - x2) <= tol and y1 - tol <= py <= y2 + tol:
            return True

        if abs(py - y1) <= tol and x1 - tol <= px <= x2 + tol:
            return True

        if abs(py - y2) <= tol and x1 - tol <= px <= x2 + tol:
            return True

        return False

    # -------------------------------------------------

    def move(self, dx, dy):

        self._set(

            self.p1,

            self._x(self.p1) + dx,

            self._y(self.p1) + dy

        )

        self._set(

            self.p2,

            self._x(self.p2) + dx,

            self._y(self.p2) + dy

        )

    # -------------------------------------------------

    def clone(self):

        if callable(getattr(self.p1, "x", None)):

            return Rectangle(

                QPoint(

                    int(self._x(self.p1)),
                    int(self._y(self.p1))

                ),

                QPoint(

                    int(self._x(self.p2)),
                    int(self._y(self.p2))

                )

            )

        return Rectangle(

            self.p1.__class__(

                self._x(self.p1),
                self._y(self.p1)

            ),

            self.p2.__class__(

                self._x(self.p2),
                self._y(self.p2)

            )

        )