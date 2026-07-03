from engine.recognition.gesture import Gesture

from engine.recognition.bounding_box import BoundingBox
from engine.recognition.aspect_ratio import AspectRatio
from engine.recognition.roundness import Roundness
from engine.recognition.edge_detector import EdgeDetector
from engine.recognition.corner_detector import CornerDetector


class ShapeClassifier:

    def __init__(self):

        self.box = BoundingBox()
        self.aspect = AspectRatio()
        self.roundness = Roundness()
        self.edges = EdgeDetector()
        self.corners = CornerDetector()

    # ----------------------------------------------------

    def classify(self, stroke):

        points = stroke.points

        if len(points) < 2:
            return Gesture.UNKNOWN

        # -------------------------
        # OPEN SHAPES
        # -------------------------

        if not stroke.is_closed():

            return Gesture.LINE

        # -------------------------
        # CLOSED SHAPES
        # -------------------------

        bbox = self.box.calculate(points)

        ratio = self.aspect.calculate(bbox)

        edge_count = len(

            self.edges.detect(points)

        )

        corner_count = len(

            self.corners.detect(points)

        )

        roundness = self.roundness.calculate(

            points,

            bbox

        )

        print()

        print("Edges :", edge_count)

        print("Corners :", corner_count)

        print("Aspect :", ratio)

        print("Roundness :", roundness)

        print()

        # -------------------------
        # Rectangle
        # -------------------------

        if edge_count == 4:

            return Gesture.RECTANGLE

        # -------------------------
        # Circle
        # -------------------------

        if roundness > 0.85:

            return Gesture.CIRCLE

        # -------------------------
        # Polygon
        # -------------------------

        if edge_count > 4:

            return Gesture.POLYGON

        return Gesture.UNKNOWN