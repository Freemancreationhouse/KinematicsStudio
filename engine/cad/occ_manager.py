from OCP.BRepPrimAPI import (
    BRepPrimAPI_MakeBox,
    BRepPrimAPI_MakeCylinder,
    BRepPrimAPI_MakeSphere,
)
from OCP.gp import gp_Pnt


class OCCManager:
    """Central OpenCascade shape manager."""

    def __init__(self):
        self._shapes = []

    # -----------------------------------------

    def clear(self):
        self._shapes.clear()

    # -----------------------------------------

    @property
    def shapes(self):
        return self._shapes

    # -----------------------------------------

    def add(self, shape):
        self._shapes.append(shape)
        return shape

    # -----------------------------------------

    def remove(self, shape):
        if shape in self._shapes:
            self._shapes.remove(shape)
            return True

        return False

    # -----------------------------------------

    def box(
        self,
        width=100,
        depth=100,
        height=100,
    ):
        shape = (
            BRepPrimAPI_MakeBox(
                gp_Pnt(0, 0, 0),
                width,
                depth,
                height,
            ).Shape()
        )

        return self.add(shape)

    # -----------------------------------------

    def cylinder(
        self,
        radius=50,
        height=100,
    ):
        shape = (
            BRepPrimAPI_MakeCylinder(
                radius,
                height,
            ).Shape()
        )

        return self.add(shape)

    # -----------------------------------------

    def sphere(
        self,
        radius=50,
    ):
        shape = (
            BRepPrimAPI_MakeSphere(
                radius
            ).Shape()
        )

        return self.add(shape)
