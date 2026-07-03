from engine.geometry import Vector2


class Camera:

    def __init__(self):

        self.position = Vector2(0, 0)

        self.zoom = 1.0

    # --------------------------------

    def pan(self, dx, dy):

        self.position.x += dx
        self.position.y += dy

    # --------------------------------

    def zoom_in(self, factor=1.1):

        self.zoom *= factor

    # --------------------------------

    def zoom_out(self, factor=1.1):

        self.zoom /= factor

    # --------------------------------

    def world_to_screen(self, point):

        return Vector2(

            (point.x - self.position.x) * self.zoom,

            (point.y - self.position.y) * self.zoom

        )

    # --------------------------------

    def screen_to_world(self, point):

        return Vector2(

            point.x / self.zoom + self.position.x,

            point.y / self.zoom + self.position.y

        )