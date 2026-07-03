from engine.generator.line_generator import LineGenerator
from engine.generator.rectangle_generator import RectangleGenerator
from engine.generator.circle_generator import CircleGenerator


class GeometryGenerator:

    def __init__(self):

        self.line = LineGenerator()

        self.rectangle = RectangleGenerator()

        self.circle = CircleGenerator()

    # -------------------------------------

    def generate(self, intent, stroke):

        shape = intent.shape

        if shape == "line":

            return self.line.generate(stroke)

        if shape == "rectangle":

            return self.rectangle.generate(stroke)

        if shape == "circle":

            return self.circle.generate(stroke)

        return None