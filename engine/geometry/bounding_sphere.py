from engine.geometry.vector3 import Vector3


class BoundingSphere:
    """Bounding sphere for coarse 3D culling and future picking."""

    def __init__(self, center=None, radius=0.0):

        self.center = center or Vector3()
        self.radius = float(radius)

    # --------------------------------

    @staticmethod
    def from_box(box):
        """Create a sphere enclosing a 3D bounding box."""

        center = box.center
        radius = max((corner.distance_to(center) for corner in box.corners()), default=0.0)

        return BoundingSphere(center, radius)
