class Confidence:

    def calculate(self, shape):

        scores = {

            "line":0.98,

            "rectangle":0.95,

            "circle":0.94,

            "polygon":0.90,

            "unknown":0.20

        }

        return scores.get(shape,0.0)