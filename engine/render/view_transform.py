from engine.geometry import Vector2


class ViewTransform:

    def __init__(self, camera):

        self.camera = camera

    # --------------------------------

    def world_to_screen(self, point):

        return self.camera.world_to_screen(point)

    # --------------------------------

    def screen_to_world(self, point):

        return self.camera.screen_to_world(point)

    # --------------------------------

    def world_distance(self, value):

        return value * self.camera.zoom

    # --------------------------------

    def screen_distance(self, value):

        return value / self.camera.zoom