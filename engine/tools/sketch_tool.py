from engine.recognition.stroke import Stroke
from engine.recognition.recognizer import Recognizer


class SketchTool:

    def __init__(self):

        self.stroke = Stroke()

        self.recognizer = Recognizer()

        self.drawing = False

    # -----------------------------------

    def mouse_press(self, canvas, event):

        self.stroke.clear()

        self.stroke.add(
            event.world_pos.x(),
            event.world_pos.y()
        )

        self.drawing = True

    # -----------------------------------

    def mouse_move(self, canvas, event):

        if not self.drawing:
            return

        self.stroke.add(
            event.world_pos.x(),
            event.world_pos.y()
        )

    # -----------------------------------

    def mouse_release(self, canvas, event):

        if not self.drawing:
            return

        self.drawing = False

        shape = self.recognizer.recognize(self.stroke)

        print("Detected :", shape)

    # -----------------------------------

    def draw_preview(self, painter):

        if self.stroke.count() < 2:
            return

        painter.setPen(painter.pen())

        pts = self.stroke.points

        for i in range(len(pts)-1):

            painter.drawLine(

                int(pts[i].x),
                int(pts[i].y),

                int(pts[i+1].x),
                int(pts[i+1].y)

            )