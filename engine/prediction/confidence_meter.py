class ConfidenceMeter:

    def color(self, confidence):

        if confidence >= 0.90:
            return (0, 255, 0)

        if confidence >= 0.75:
            return (255, 220, 0)

        return (255, 80, 80)