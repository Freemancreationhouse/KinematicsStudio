from engine.entities import RectangleEntity
from engine.geometry import Vector2


class RectangleGenerator:

    def generate(self, stroke):

        if len(stroke.points) < 2:
            return None

        xs = [p.x for p in stroke.points]
        ys = [p.y for p in stroke.points]

        return RectangleEntity(

            Vector2(
                min(xs),
                min(ys)
            ),

            Vector2(
                max(xs),
                max(ys)
            )

        )