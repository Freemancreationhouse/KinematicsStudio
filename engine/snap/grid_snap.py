from PySide6.QtCore import QPoint


class GridSnap:

    def __init__(self, grid_size=25):
        self.grid_size = grid_size

    def snap(self, point):

        x = round(point.x() / self.grid_size) * self.grid_size
        y = round(point.y() / self.grid_size) * self.grid_size

        return QPoint(x, y)