class AspectRatio:

    def calculate(self, bbox):

        w = bbox["width"]
        h = bbox["height"]

        if h == 0:
            return 0

        return w / h