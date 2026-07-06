GEOMETRY_EPSILON = 1.0e-9


def nearly_equal(a, b, epsilon=GEOMETRY_EPSILON):
    """Return True when two scalar values are within geometry tolerance."""

    return abs(a - b) <= epsilon


def is_zero(value, epsilon=GEOMETRY_EPSILON):
    """Return True when a scalar value is effectively zero."""

    return abs(value) <= epsilon


def within(value, lower, upper, epsilon=GEOMETRY_EPSILON):
    """Return True when a value is within inclusive bounds plus tolerance."""

    return lower - epsilon <= value <= upper + epsilon
