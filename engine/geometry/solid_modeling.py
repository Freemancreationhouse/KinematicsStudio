import math

from engine.geometry.primitives3d import MeshBuilder
from engine.geometry.vector3 import Vector3


def extrude_profile(profile=None, distance=100.0, symmetric=False, direction="Positive"):
    """Create a closed prismatic mesh by extruding a planar profile along Z."""

    points = _closed_profile(profile) or _rectangle_profile(100.0, 60.0)
    span = _signed_distance(distance, direction)
    bottom_z = -span * 0.5 if symmetric else 0.0
    top_z = span * 0.5 if symmetric else span
    return _mesh_between_sections(
        [_with_z(point, bottom_z) for point in points],
        [_with_z(point, top_z) for point in points],
        cap_start=True,
        cap_end=True,
    )


def revolve_profile(profile=None, angle=360.0, segments=36, axis="Z"):
    """Create a surface of revolution mesh from a 2D profile."""

    points = _open_profile(profile) or [Vector3(40.0, -40.0, 0.0), Vector3(40.0, 40.0, 0.0)]
    total_angle = math.radians(float(angle or 360.0))
    segment_count = max(int(abs(total_angle) / (math.pi * 2.0) * segments), 3)
    if abs(abs(total_angle) - math.pi * 2.0) < 1.0e-6:
        segment_count = max(int(segments), 12)
    rows = []

    for index in range(segment_count + 1):
        theta = total_angle * index / segment_count
        rows.append([_rotate_around_axis(point, theta, axis) for point in points])

    return _loft_sections(rows, close_around=abs(abs(total_angle) - math.pi * 2.0) < 1.0e-6)


def sweep_profile(profile=None, path=None, segments=16):
    """Create a swept mesh by carrying a profile along a polyline path."""

    section = _closed_profile(profile) or _circle_profile(18.0, max(int(segments), 8))
    path_points = _path_points(path) or [Vector3(0.0, -60.0, 0.0), Vector3(0.0, 60.0, 0.0)]
    sections = []

    for path_point in path_points:
        sections.append([Vector3(path_point.x + p.x, path_point.y + p.y, path_point.z + p.z) for p in section])

    return _loft_sections(sections, cap_start=True, cap_end=True)


def loft_profiles(profiles=None):
    """Create a lofted mesh through two or more compatible profiles."""

    sections = [_closed_profile(profile) for profile in profiles or []]
    sections = [section for section in sections if section]
    if len(sections) < 2:
        sections = [
            _translate(_rectangle_profile(80.0, 50.0), Vector3(0.0, 0.0, -40.0)),
            _translate(_circle_profile(45.0, 16), Vector3(0.0, 0.0, 40.0)),
        ]
    sections = _compatible_sections(sections)
    return _loft_sections(sections, cap_start=True, cap_end=True)


def mesh_statistics(mesh_data):
    """Return mesh quality statistics for diagnostics and certification."""

    return {
        "vertices": len(getattr(mesh_data, "vertices", [])),
        "edges": len(getattr(mesh_data, "edges", [])),
        "faces": len(getattr(mesh_data, "faces", [])),
        "triangles": len(getattr(mesh_data, "triangle_indices", [])),
    }


def _mesh_between_sections(start, end, cap_start=False, cap_end=False):
    return _loft_sections([start, end], cap_start=cap_start, cap_end=cap_end)


def _loft_sections(sections, cap_start=False, cap_end=False, close_around=False):
    if len(sections) < 2:
        raise ValueError("At least two sections are required.")

    sections = _compatible_sections(sections)
    builder = MeshBuilder()
    grid = []

    for section in sections:
        grid.append([builder.add_vertex(point) for point in section])

    section_count = len(grid)
    profile_count = len(grid[0])
    ring_count = section_count if close_around else section_count - 1

    for row in range(ring_count):
        next_row = (row + 1) % section_count
        for index in range(profile_count):
            builder.add_quad(
                grid[row][index],
                grid[row][(index + 1) % profile_count],
                grid[next_row][(index + 1) % profile_count],
                grid[next_row][index],
            )

    if cap_start and not close_around:
        builder.add_face(list(reversed(grid[0])))

    if cap_end and not close_around:
        builder.add_face(grid[-1])

    return builder.build()


def _closed_profile(profile):
    points = _coerce_points(profile)
    if len(points) < 3:
        return []
    if points[0].distance_to(points[-1]) <= 1.0e-6:
        points = points[:-1]
    return points if len(points) >= 3 else []


def _open_profile(profile):
    points = _coerce_points(profile)
    return points if len(points) >= 2 else []


def _path_points(path):
    points = _coerce_points(path)
    return points if len(points) >= 2 else []


def _coerce_points(value):
    if value is None:
        return []
    if hasattr(value, "points"):
        candidate = value.points
        value = candidate() if callable(candidate) else candidate
    points = []
    for item in value or []:
        if isinstance(item, Vector3):
            points.append(item.copy())
        elif hasattr(item, "x") and hasattr(item, "y"):
            points.append(Vector3(item.x, item.y, getattr(item, "z", 0.0)))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            points.append(Vector3(item[0], item[1], item[2] if len(item) > 2 else 0.0))
    return points


def _compatible_sections(sections):
    count = max(len(section) for section in sections)
    return [_resample_closed(section, count) for section in sections]


def _resample_closed(points, count):
    if len(points) == count:
        return [point.copy() for point in points]
    result = []
    size = len(points)
    for index in range(count):
        position = index * size / count
        left = int(math.floor(position)) % size
        right = (left + 1) % size
        t = position - math.floor(position)
        result.append(points[left] * (1.0 - t) + points[right] * t)
    return result


def _rectangle_profile(width, depth):
    hw = float(width) * 0.5
    hd = float(depth) * 0.5
    return [
        Vector3(-hw, -hd, 0.0),
        Vector3(hw, -hd, 0.0),
        Vector3(hw, hd, 0.0),
        Vector3(-hw, hd, 0.0),
    ]


def _circle_profile(radius, segments):
    return [
        Vector3(radius * math.cos(2.0 * math.pi * index / segments), radius * math.sin(2.0 * math.pi * index / segments), 0.0)
        for index in range(segments)
    ]


def _translate(points, delta):
    return [point + delta for point in points]


def _with_z(point, z):
    return Vector3(point.x, point.y, z)


def _signed_distance(distance, direction):
    value = float(distance or 0.0)
    if str(direction).lower().startswith("neg"):
        value = -abs(value)
    return value


def _rotate_around_axis(point, theta, axis):
    axis = str(axis or "Z").upper()
    c = math.cos(theta)
    s = math.sin(theta)
    if axis == "X":
        return Vector3(point.x, point.y * c - point.z * s, point.y * s + point.z * c)
    if axis == "Y":
        return Vector3(point.x * c + point.z * s, point.y, -point.x * s + point.z * c)
    return Vector3(point.x * c - point.y * s, point.x * s + point.y * c, point.z)
