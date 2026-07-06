from engine.entities import LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.geometry.extend import extend_entities
from engine.geometry.mirror import mirror_entities
from engine.geometry.offset import offset_entities
from engine.geometry.primitives import (
    infinite_line_intersection,
    is_degenerate_segment,
    point_to_segment_distance,
    rectangle_edges,
    segment_intersection,
    signed_distance_to_line,
)
from engine.geometry.rotate import rotate_entities
from engine.geometry.tolerance import GEOMETRY_EPSILON
from engine.geometry.trim import trim_entities


def close(a, b, tolerance=1.0e-6):

    assert abs(a - b) <= tolerance


parallel = segment_intersection(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(0, 1),
    Vector2(10, 1),
)
assert parallel is None

nearly_parallel = infinite_line_intersection(
    Vector2(0, 0),
    Vector2(1, 0),
    Vector2(0, GEOMETRY_EPSILON * 0.1),
    Vector2(1, GEOMETRY_EPSILON * 0.1),
)
assert nearly_parallel is None

shared_endpoint = segment_intersection(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(10, 0),
    Vector2(10, 10),
)
assert shared_endpoint is not None
close(shared_endpoint.x, 10)
close(shared_endpoint.y, 0)

assert is_degenerate_segment(Vector2(0, 0), Vector2(GEOMETRY_EPSILON * 0.1, 0))
close(point_to_segment_distance(Vector2(1, 1), Vector2(0, 0), Vector2(0, 0)), 2 ** 0.5)

reversed_rect = RectangleEntity(Vector2(10, 10), Vector2(0, 0))
edges = rectangle_edges(reversed_rect)
assert len(edges) == 4
close(edges[0][0].x, 10)
close(edges[2][0].x, 0)

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
cutter = LineEntity(Vector2(5, -5), Vector2(5, 5))
trimmed = trim_entities(line, cutter, Vector2(1, 0))
assert trimmed and trimmed[0].start.x == 5

extended = extend_entities(
    LineEntity(Vector2(0, 0), Vector2(1, 0)),
    LineEntity(Vector2(2, -1), Vector2(2, 1)),
    Vector2(1, 0),
)
assert extended and extended[0].end.x == 2

small_offset = offset_entities(
    LineEntity(Vector2(0, 0), Vector2(1.0e-6, 0)),
    Vector2(0, 1.0e-6),
)
assert small_offset is not None

large_rotated = rotate_entities(
    LineEntity(Vector2(1.0e9, 0), Vector2(1.0e9 + 10, 0)),
    Vector2(1.0e9, 0),
    90,
)
assert large_rotated is not None
close(large_rotated[0].start.x, 1.0e9)
close(large_rotated[0].end.y, 10)

mirrored = mirror_entities(
    RectangleEntity(Vector2(10, 10), Vector2(0, 0)),
    Vector2(0, 0),
    Vector2(0, 10),
)
assert mirrored and hasattr(mirrored[0], "p1")
close(mirrored[0].p1.x, -10)

signed = signed_distance_to_line(Vector2(0, 0), Vector2(10, 0), Vector2(0, 5))
close(signed, 5)

print("geometry-foundation-ok")
