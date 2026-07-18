import math

from engine.geometry import BoundingBox, Vector2


DEFAULT_TEXT = "Text"
DEFAULT_MTEXT = "MText"
DEFAULT_LEADER_TEXT = "Leader"
DEFAULT_TEXT_HEIGHT = 20.0
TEXT_WIDTH_FACTOR = 0.6


def copy_entity_metadata(source, target):
    """Copy common entity display and layer state between annotation entities."""

    target.selected = getattr(source, "selected", False)
    target.visible = getattr(source, "visible", True)
    target.locked = getattr(source, "locked", False)
    target.layer = getattr(source, "layer", None)
    target.layer_id = getattr(source, "layer_id", None)
    target.layer_name = getattr(source, "layer_name", None)
    target.color = getattr(source, "color", None)


def normalized_lines(text):
    """Return non-empty drawable text lines while preserving multiline intent."""

    lines = str(text or "").splitlines()

    return lines or [""]


def text_width(text, height):
    """Estimate text width in world units for hit testing and preview bounds."""

    return max(len(str(text or "")), 1) * max(float(height), 1.0) * TEXT_WIDTH_FACTOR


def text_block_size(lines, height):
    """Return approximate multiline text dimensions in world units."""

    line_height = max(float(height), 1.0)
    width = max(text_width(line, line_height) for line in (lines or [""]))

    return width, line_height * max(len(lines or [""]), 1)


def wrapped_lines(text, box_width, text_height):
    """Wrap text into lines using the shared annotation width approximation."""

    max_chars = max(1, int(max(float(box_width), 1.0) / (max(text_height, 1.0) * TEXT_WIDTH_FACTOR)))
    output = []

    for source in normalized_lines(text):
        words = source.split(" ")
        line = ""

        for word in words:
            candidate = word if not line else f"{line} {word}"

            if len(candidate) <= max_chars:
                line = candidate
                continue

            if line:
                output.append(line)

            line = word

            while len(line) > max_chars:
                output.append(line[:max_chars])
                line = line[max_chars:]

        output.append(line)

    return output or [""]


def rotated_point(point, origin, degrees):
    """Rotate a point around an origin by the supplied angle in degrees."""

    radians = math.radians(float(degrees))
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    dx = point.x - origin.x
    dy = point.y - origin.y

    return Vector2(
        origin.x + dx * cos_a - dy * sin_a,
        origin.y + dx * sin_a + dy * cos_a,
    )


def unrotated_point(point, origin, degrees):
    """Transform a world point into local annotation coordinates."""

    return rotated_point(point, origin, -float(degrees))


def box_from_points(points):
    """Build a bounding box from a sequence of Vector2 points."""

    box = BoundingBox()

    for point in points:
        box.add(point)

    return box


def rotated_box(origin, width, height, degrees):
    """Return a world-space bounding box for a rotated rectangular area."""

    corners = [
        origin.copy(),
        Vector2(origin.x + width, origin.y),
        Vector2(origin.x + width, origin.y + height),
        Vector2(origin.x, origin.y + height),
    ]

    return box_from_points(rotated_point(corner, origin, degrees) for corner in corners)


def point_in_local_box(point, origin, width, height, degrees, tolerance=5.0):
    """Return True when a point is inside a rotated annotation box."""

    local = unrotated_point(point, origin, degrees)

    return (
        origin.x - tolerance <= local.x <= origin.x + width + tolerance and
        origin.y - tolerance <= local.y <= origin.y + height + tolerance
    )


def point_to_segment_distance(point, start, end):
    """Return the shortest distance from a point to a finite segment."""

    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        return point.distance_to(start)

    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    nearest = Vector2(start.x + t * dx, start.y + t * dy)

    return nearest.distance_to(point)
