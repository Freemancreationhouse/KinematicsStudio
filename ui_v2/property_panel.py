from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
)

import math


class PropertyPanel(QWidget):

    def __init__(self):

        super().__init__()

        layout = QFormLayout(self)

        self.type = QLineEdit()
        self.type.setReadOnly(True)

        self.x = QLineEdit()
        self.y = QLineEdit()

        self.x2 = QLineEdit()
        self.y2 = QLineEdit()

        self.length = QLineEdit()

        self.angle = QLineEdit()

        for w in [

            self.x,
            self.y,
            self.x2,
            self.y2,
            self.length,
            self.angle,

        ]:

            w.setReadOnly(True)

        layout.addRow("Type", self.type)
        layout.addRow("X1", self.x)
        layout.addRow("Y1", self.y)
        layout.addRow("X2", self.x2)
        layout.addRow("Y2", self.y2)
        layout.addRow("Length", self.length)
        layout.addRow("Angle", self.angle)

    # -----------------------------------------

    def clear(self):

        self.type.setText("None")

        self.x.clear()
        self.y.clear()

        self.x2.clear()
        self.y2.clear()

        self.length.clear()

        self.angle.clear()

    # -----------------------------------------

    def show_selection(self, selected):

        if not selected:
            self.clear()
            return

        if len(selected) > 1:
            self.clear()
            self.type.setText(f"Multiple ({len(selected)})")
            return

        entity = selected[0]

        self.clear()
        self.type.setText(entity.type_name)

        if hasattr(entity, "start") and hasattr(entity, "end"):
            self._set_point_pair(entity.start, entity.end)
            dx = entity.end.x - entity.start.x
            dy = entity.end.y - entity.start.y
            self.length.setText(self._number(math.hypot(dx, dy)))
            self.angle.setText(self._number(math.degrees(math.atan2(dy, dx))))

        elif hasattr(entity, "p1") and hasattr(entity, "p2"):
            self._set_point_pair(entity.p1, entity.p2)
            self.length.setText(
                f"W {self._number(entity.width)}  H {self._number(entity.height)}"
            )

        elif hasattr(entity, "center") and hasattr(entity, "radius"):
            self.x.setText(self._number(entity.center.x))
            self.y.setText(self._number(entity.center.y))
            self.length.setText(f"R {self._number(entity.radius)}")

    # -----------------------------------------

    def _set_point_pair(self, p1, p2):

        self.x.setText(self._number(p1.x))
        self.y.setText(self._number(p1.y))
        self.x2.setText(self._number(p2.x))
        self.y2.setText(self._number(p2.y))

    # -----------------------------------------

    def _number(self, value):

        return f"{value:.2f}"
