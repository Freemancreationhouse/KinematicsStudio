from math import sqrt

from engine.entities import CircleEntity
from engine.geometry import Vector2


class CircleGenerator:

    def generate(self, stroke):

        if len(stroke.points) < 2:
            return None

        xs = [p.x for p in stroke.points]
        ys = [p.y for p in stroke.points]

        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)

        radius = 0.0

        for p in stroke.points:

            dx = p.x - cx
            dy = p.y - cy

            radius += sqrt(dx * dx + dy * dy)

        radius /= len(stroke.points)

        return CircleEntity(

            Vector2(
                cx,
                cy
            ),

            radius

        )