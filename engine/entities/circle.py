# DEPRECATED: Legacy circle entity retained for backward compatibility.
# V2 uses engine.entities.circle_entity.CircleEntity.

from math import sqrt

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPen


class Circle:

    def __init__(self, center, radius):

        self.center = center
        self.radius = radius

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
            painter.setPen(QPen(QColor("#FFAA00"), 2))

        painter.drawEllipse(

            QPoint(

                int(self._x(self.center)),
                int(self._y(self.center))

            ),

            int(self.radius),

            int(self.radius)

        )

    # -------------------------------------------------

    def hit_test(self, p):

        d = sqrt(

            (p.x() - self._x(self.center)) ** 2 +

            (p.y() - self._y(self.center)) ** 2

        )

        return abs(d - self.radius) <= 6

    # -------------------------------------------------

    def move(self, dx, dy):

        self._set(

            self.center,

            self._x(self.center) + dx,

            self._y(self.center) + dy

        )

    # -------------------------------------------------

    def clone(self):

        if callable(getattr(self.center, "x", None)):

            return Circle(

                QPoint(

                    int(self._x(self.center)),
                    int(self._y(self.center))

                ),

                self.radius

            )

        return Circle(

            self.center.__class__(

                self._x(self.center),

                self._y(self.center)

            ),

            self.radius

        )
