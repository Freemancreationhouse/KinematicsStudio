from engine.geometry import Vector2


class GridSnap:

    def __init__(self, grid_size=25):

        self.grid_size = grid_size

    def snap(self, point):

        return Vector2(
            round(point.x / self.grid_size) * self.grid_size,
            round(point.y / self.grid_size) * self.grid_size
        )
