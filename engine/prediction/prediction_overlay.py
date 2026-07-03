from PySide6.QtGui import QColor, QFont


class PredictionOverlay:

    def draw(self, painter, prediction, mouse_pos):

        if prediction is None:
            return

        painter.setPen(QColor(0, 255, 120))

        font = QFont()

        font.setPointSize(12)

        font.setBold(True)

        painter.setFont(font)

        text = f"{prediction['shape'].upper()}  {prediction['confidence']*100:.0f}%"

        painter.drawText(

            int(mouse_pos.x()) + 15,

            int(mouse_pos.y()) - 15,

            text

        )