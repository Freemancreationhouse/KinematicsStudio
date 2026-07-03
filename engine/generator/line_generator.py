from engine.entities import LineEntity
from engine.geometry import Vector2


class LineGenerator:

    def generate(self, stroke):

        if len(stroke.points) < 2:
            return None

        return LineEntity(

            Vector2(
                stroke.points[0].x,
                stroke.points[0].y
            ),

            Vector2(
                stroke.points[-1].x,
                stroke.points[-1].y
            )

        )