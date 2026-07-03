class StrokeSmoother:

    def smooth(self, points):

        if len(points) < 3:
            return points

        result = [points[0]]

        for i in range(1, len(points)-1):

            p0 = points[i-1]
            p1 = points[i]
            p2 = points[i+1]

            x = (p0.x + p1.x + p2.x) / 3
            y = (p0.y + p1.y + p2.y) / 3

            result.append(
                p1.__class__(x, y)
            )

        result.append(points[-1])

        return result