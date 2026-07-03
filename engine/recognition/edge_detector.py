from math import atan2, degrees


class EdgeDetector:

    def detect(self, points):

        if len(points) < 3:
            return []

        edges = []

        start = 0

        last_angle = None

        threshold = 12

        for i in range(1, len(points)):

            dx = points[i].x - points[i - 1].x
            dy = points[i].y - points[i - 1].y

            if dx == 0 and dy == 0:
                continue

            angle = degrees(atan2(dy, dx))

            if last_angle is None:

                last_angle = angle
                continue

            if abs(angle - last_angle) > threshold:

                edges.append({

                    "start": start,

                    "end": i - 1,

                    "angle": last_angle

                })

                start = i - 1

                last_angle = angle

        edges.append({

            "start": start,

            "end": len(points) - 1,

            "angle": last_angle

        })

        return edges