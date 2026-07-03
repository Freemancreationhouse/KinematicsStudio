class BoundingBox:

    def calculate(self, points):

        if not points:
            return None

        xs = [p.x for p in points]
        ys = [p.y for p in points]

        return {

            "xmin": min(xs),
            "xmax": max(xs),

            "ymin": min(ys),
            "ymax": max(ys),

            "width": max(xs) - min(xs),
            "height": max(ys) - min(ys),

            "center_x": (min(xs) + max(xs)) / 2,
            "center_y": (min(ys) + max(ys)) / 2

        }