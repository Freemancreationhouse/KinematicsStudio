from engine.recognition.stroke_smoother import StrokeSmoother
from engine.recognition.stroke_simplifier import StrokeSimplifier
from engine.recognition.corner_detector import CornerDetector


class StrokeProcessor:

    def __init__(self):

        self.smoother = StrokeSmoother()

        self.simplifier = StrokeSimplifier()

        self.corner_detector = CornerDetector()

    # -----------------------------------

    def process(self, stroke):

        pts = stroke.points

        pts = self.smoother.smooth(pts)

        pts = self.simplifier.simplify(pts)

        corners = self.corner_detector.detect(pts)

        return {

            "points": pts,

            "corners": corners

        }