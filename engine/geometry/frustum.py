from engine.geometry.plane import Plane


class Frustum:
    """Camera frustum represented by clipping planes."""

    def __init__(self, planes=None):

        self.planes = list(planes or [])

    # --------------------------------

    def contains_sphere(self, sphere):
        """Return True when a sphere intersects or lies inside the frustum."""

        for plane in self.planes:
            if plane.signed_distance(sphere.center) < -sphere.radius:
                return False

        return True

    # --------------------------------

    @staticmethod
    def empty():
        """Return a permissive frustum until extraction is needed."""

        return Frustum([
            Plane(),
        ])
