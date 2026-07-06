from engine.geometry import Vector2
from engine.geometry.primitives import (
    ENDPOINT_END,
    ENDPOINT_INTERIOR,
    ENDPOINT_OFF,
    ENDPOINT_START,
    INTERSECTION_COINCIDENT,
    INTERSECTION_CROSS,
    INTERSECTION_OVERLAP,
    INTERSECTION_PARALLEL,
    INTERSECTION_TOUCH,
    are_collinear_segments,
    classify_segment_intersection,
    endpoint_classification,
    intersection_classification,
    overlapping_segment,
    segment_classification,
    segments_overlap,
)
from engine.geometry.tolerance import GEOMETRY_EPSILON


def close(a, b, tolerance=1.0e-6):

    assert abs(a - b) <= tolerance


assert segment_classification(
    Vector2(0, 0),
    Vector2(GEOMETRY_EPSILON * 0.1, 0),
) == "DEGENERATE"

assert are_collinear_segments(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(2, 0),
    Vector2(8, 0),
)

contained = overlapping_segment(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(2, 0),
    Vector2(8, 0),
)
assert contained is not None
close(contained[0].x, 2)
close(contained[1].x, 8)

partial = overlapping_segment(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(5, 0),
    Vector2(15, 0),
)
assert partial is not None
close(partial[0].x, 5)
close(partial[1].x, 10)

assert segments_overlap(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(5, 0),
    Vector2(15, 0),
)

touch = intersection_classification(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(10, 0),
    Vector2(20, 0),
)
assert touch["type"] == INTERSECTION_TOUCH
close(touch["point"].x, 10)

coincident = intersection_classification(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(0, 0),
    Vector2(10, 0),
)
assert coincident["type"] == INTERSECTION_OVERLAP

parallel = classify_segment_intersection(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(0, 1),
    Vector2(10, 1),
)
assert parallel == INTERSECTION_PARALLEL

cross = classify_segment_intersection(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(5, -5),
    Vector2(5, 5),
)
assert cross == INTERSECTION_CROSS

disjoint_collinear = classify_segment_intersection(
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(20, 0),
    Vector2(30, 0),
)
assert disjoint_collinear == INTERSECTION_COINCIDENT

tiny = intersection_classification(
    Vector2(0, 0),
    Vector2(1.0e-8, 0),
    Vector2(5.0e-9, -1.0e-8),
    Vector2(5.0e-9, 1.0e-8),
)
assert tiny["type"] == INTERSECTION_CROSS

huge = intersection_classification(
    Vector2(1.0e12, 0),
    Vector2(1.0e12 + 1000, 0),
    Vector2(1.0e12 + 500, -1000),
    Vector2(1.0e12 + 500, 1000),
)
assert huge["type"] == INTERSECTION_CROSS
close(huge["point"].x, 1.0e12 + 500, 1.0e-3)

assert endpoint_classification(Vector2(0, 0), Vector2(0, 0), Vector2(10, 0)) == ENDPOINT_START
assert endpoint_classification(Vector2(10, 0), Vector2(0, 0), Vector2(10, 0)) == ENDPOINT_END
assert endpoint_classification(Vector2(5, 0), Vector2(0, 0), Vector2(10, 0)) == ENDPOINT_INTERIOR
assert endpoint_classification(Vector2(5, 1), Vector2(0, 0), Vector2(10, 0)) == ENDPOINT_OFF

print("geometry-maintenance2-ok")
