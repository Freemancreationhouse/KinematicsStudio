from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
)


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