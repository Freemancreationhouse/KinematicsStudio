from math import sqrt


class SnapManager:

    def __init__(self):

        self.endpoint = True
        self.midpoint = True
        self.center = True
        self.intersection = False

    # ------------------------------------------------------------

    def snap(self, point, project):

        nearest = point
        best = 12

        # ---------------- Endpoint / Midpoint / Center ----------------

        for entity in project.entities:

            # -------- LINE --------

            if hasattr(entity, "start"):

                if self.endpoint:

                    for p in entity.endpoints():

                        d = sqrt(
                            (point.x() - p.x()) ** 2 +
                            (point.y() - p.y()) ** 2
                        )

                        if d < best:
                            best = d
                            nearest = p

                if self.midpoint:

                    p = entity.midpoint()

                    d = sqrt(
                        (point.x() - p.x()) ** 2 +
                        (point.y() - p.y()) ** 2
                    )

                    if d < best:
                        best = d
                        nearest = p

            # -------- RECTANGLE --------

            elif hasattr(entity, "p1"):

                if self.endpoint:

                    x1 = entity.p1.x()
                    y1 = entity.p1.y()

                    x2 = entity.p2.x()
                    y2 = entity.p2.y()

                    pts = [

                        entity.p1,

                        entity.p2,

                        entity.p1.__class__(x1, y2),

                        entity.p1.__class__(x2, y1)

                    ]

                    for p in pts:

                        d = sqrt(
                            (point.x() - p.x()) ** 2 +
                            (point.y() - p.y()) ** 2
                        )

                        if d < best:
                            best = d
                            nearest = p

            # -------- CIRCLE --------

            elif hasattr(entity, "center"):

                if self.center:

                    d = sqrt(
                        (point.x() - entity.center.x()) ** 2 +
                        (point.y() - entity.center.y()) ** 2
                    )

                    if d < best:
                        best = d
                        nearest = entity.center

        # ---------------- Intersection ----------------

        if self.intersection:

            lines = [

                e for e in project.entities

                if hasattr(e, "intersection")

            ]

            for i in range(len(lines)):

                for j in range(i + 1, len(lines)):

                    p = lines[i].intersection(lines[j])

                    if p is None:
                        continue

                    d = sqrt(
                        (point.x() - p.x()) ** 2 +
                        (point.y() - p.y()) ** 2
                    )

                    if d < best:
                        best = d
                        nearest = p

        return nearest