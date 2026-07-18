from engine.geometry.bounding_box3d import BoundingBox3D
from engine.geometry.bounding_sphere import BoundingSphere
from engine.geometry.vector3 import Vector3


def clamp(value, minimum, maximum):
    """Clamp a numeric value into an inclusive range."""

    return max(minimum, min(maximum, value))


def lerp(a, b, amount):
    """Linearly interpolate between numeric values."""

    return a + (b - a) * amount


def box_from_points(points):
    """Return a 3D bounding box for the supplied points."""

    box = BoundingBox3D()

    for point in points:
        box.add(point)

    return box


def sphere_from_points(points):
    """Return a bounding sphere for the supplied points."""

    return BoundingSphere.from_box(box_from_points(points))


WORLD_UP = Vector3(0.0, 0.0, 1.0)
WORLD_RIGHT = Vector3(1.0, 0.0, 0.0)
WORLD_FORWARD = Vector3(0.0, 1.0, 0.0)
