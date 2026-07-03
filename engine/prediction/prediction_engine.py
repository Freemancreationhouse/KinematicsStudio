from engine.recognition.recognizer import Recognizer


class PredictionEngine:

    def __init__(self):

        self.recognizer = Recognizer()

    def predict(self, stroke):

        if len(stroke.points) < 5:
            return None

        return self.recognizer.recognize(stroke)