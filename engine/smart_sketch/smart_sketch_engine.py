from engine.smart_sketch.sketch_session import SketchSession
from engine.smart_sketch.stroke_processor import StrokeProcessor

from engine.recognition.recognizer import Recognizer
from engine.intent.intent_engine import IntentEngine
from engine.smart_sketch.geometry_builder import GeometryBuilder


class SmartSketchEngine:

    def __init__(self):

        self.processor = StrokeProcessor()
        self.recognizer = Recognizer()
        self.intent_engine = IntentEngine()
        self.builder = GeometryBuilder()

        self.reset()

    # ------------------------------------------------

    def reset(self):

        self.session = SketchSession()

    # ------------------------------------------------

    def begin(self):

        self.reset()
        self.session.begin()

    # ------------------------------------------------

    def add_point(self, point):

        self.session.add_point(point.x, point.y)

    # ------------------------------------------------

    def add(self, x, y):
        """Add a point using the legacy Smart Sketch coordinate API."""

        self.session.add_point(x, y)

    # ------------------------------------------------

    def finish(self):

        stroke = self.session.stroke

        self.processor.process(stroke)

        recognition = self.recognizer.recognize(stroke)

        intent = self.intent_engine.analyze(
            recognition
        )

        entity = self.builder.build(
            intent,
            stroke
        )

        return {
            "intent": intent.shape,
            "entity": entity
        }
