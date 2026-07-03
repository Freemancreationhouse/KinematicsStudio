class Prediction:

    def __init__(self):

        self.name = ""

        self.score = 0.0

    def __repr__(self):

        return f"{self.name} ({self.score:.2f})"