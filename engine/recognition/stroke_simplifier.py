from math import sqrt


class StrokeSimplifier:

    def simplify(self, points, tolerance=3):

        if len(points) < 2:
            return points

        result = [points[0]]

        last = points[0]

        for p in points[1:]:

            dx = p.x - last.x
            dy = p.y - last.y

            if sqrt(dx*dx + dy*dy) >= tolerance:

                result.append(p)
                last = p

        return result