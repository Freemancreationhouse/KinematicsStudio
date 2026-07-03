from math import acos


class CornerDetector:

    def detect(self, points):

        corners = []

        if len(points) < 3:
            return corners

        for i in range(1, len(points)-1):

            a = points[i-1]
            b = points[i]
            c = points[i+1]

            abx = a.x - b.x
            aby = a.y - b.y

            cbx = c.x - b.x
            cby = c.y - b.y

            lab = (abx*abx + aby*aby) ** 0.5
            lcb = (cbx*cbx + cby*cby) ** 0.5

            if lab == 0 or lcb == 0:
                continue

            dot = (abx*cbx + aby*cby)/(lab*lcb)

            dot = max(-1, min(1, dot))

            angle = acos(dot)

            if angle < 2.4:

                corners.append(i)

        return corners