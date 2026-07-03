from engine.recognition.stroke import Stroke


class SketchSession:

    def __init__(self):

        self.stroke = Stroke()

        self.is_drawing = False

    # -----------------------------

    def begin(self):

        self.stroke.clear()

        self.is_drawing = True

    # -----------------------------

    def add_point(self, x, y):

        self.stroke.add(x, y)

    # -----------------------------

    def end(self):

        self.is_drawing = False

    # -----------------------------

    def clear(self):

        self.stroke.clear()