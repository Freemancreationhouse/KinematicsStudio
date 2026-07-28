from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box


class OCCSelection:
    """Selection helper for OpenCascade shapes."""

    def __init__(self):
        self.selected = []
        self.hovered = None

    # --------------------------------------------------

    def clear(self):

        self.selected.clear()

        self.hovered = None

    # --------------------------------------------------

    def select(
        self,
        shape,
        additive=False,
    ):

        if shape is None:
            if not additive:
                self.clear()
            return

        if not additive:
            self.selected.clear()

        if shape not in self.selected:
            self.selected.append(shape)

    # --------------------------------------------------

    def deselect(self, shape):

        if shape in self.selected:
            self.selected.remove(shape)

    # --------------------------------------------------

    def is_selected(self, shape):

        return shape in self.selected

    # --------------------------------------------------

    def bounding_box(self, shape):

        box = Bnd_Box()

        BRepBndLib.Add(shape, box)

        return box

    # --------------------------------------------------

    def bounds(self, shape):

        xmin, ymin, zmin, xmax, ymax, zmax = self.bounding_box(shape).Get()

        return (
            xmin,
            ymin,
            zmin,
            xmax,
            ymax,
            zmax,
        )

    # --------------------------------------------------

    def center(self, shape):

        xmin, ymin, zmin, xmax, ymax, zmax = self.bounds(shape)

        return (
            (xmin + xmax) * 0.5,
            (ymin + ymax) * 0.5,
            (zmin + zmax) * 0.5,
        )

    # --------------------------------------------------

    def contains_point(
        self,
        shape,
        point,
    ):

        xmin, ymin, zmin, xmax, ymax, zmax = self.bounds(shape)

        x, y, z = point

        return (
            xmin <= x <= xmax
            and ymin <= y <= ymax
            and zmin <= z <= zmax
        )

    # --------------------------------------------------

    def first(self):

        if not self.selected:
            return None

        return self.selected[0]

    # --------------------------------------------------

    def last(self):

        if not self.selected:
            return None

        return self.selected[-1]

    # --------------------------------------------------

    def count(self):

        return len(self.selected)