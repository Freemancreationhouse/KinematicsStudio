from math import sqrt


class Roundness:

    def calculate(self, points, bbox):

        if len(points) < 3:
            return 0

        cx = bbox["center_x"]
        cy = bbox["center_y"]

        radii = []

        for p in points:

            r = sqrt(

                (p.x - cx) ** 2 +

                (p.y - cy) ** 2

            )

            radii.append(r)

        avg = sum(radii) / len(radii)

        variation = sum(

            abs(r - avg)

            for r in radii

        ) / len(radii)

        score = 1 - variation / avg

        return max(0, min(1, score))