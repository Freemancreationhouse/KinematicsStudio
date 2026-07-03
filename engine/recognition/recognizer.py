from engine.recognition.stroke_smoother import StrokeSmoother
from engine.recognition.stroke_simplifier import StrokeSimplifier
from engine.recognition.corner_detector import CornerDetector
from engine.recognition.shape_classifier import ShapeClassifier


class Recognizer:

    def __init__(self):

        self.smoother = StrokeSmoother()
        self.simplifier = StrokeSimplifier()
        self.corner_detector = CornerDetector()
        self.classifier = ShapeClassifier()

    # -----------------------------------------------------

    def recognize(self, stroke):

        points = stroke.points

        # Step 1
        points = self.smoother.smooth(points)

        # Step 2
        points = self.simplifier.simplify(points)

        # Step 3
        corners = self.corner_detector.detect(points)

        # Step 4
        shape = self.classifier.classify(stroke)

        return {

            "shape": shape,
            "points": points,
            "corners": corners

        }