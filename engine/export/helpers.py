import html
import math


def layer_for(workspace, entity):
    """Return the workspace layer assigned to an entity."""

    if hasattr(workspace, "entity_layer"):
        return workspace.entity_layer(entity)

    return getattr(entity, "layer", None)


def layer_name(item):
    """Return a safe layer name for an export item."""

    layer = getattr(item, "layer", None)

    if layer is not None:
        return getattr(layer, "name", "0")

    return getattr(item.entity, "layer_name", None) or "0"


def color_for(item):
    """Return the effective entity color as a CSS-style hex string."""

    layer = getattr(item, "layer", None)

    if layer is not None and getattr(layer, "color", None):
        return layer.color

    return getattr(item.entity, "display_color", "#e0e0e0")


def line_weight_for(item, default=1.0):
    """Return the effective line weight for an entity."""

    layer = getattr(item, "layer", None)

    if layer is not None:
        return max(0.1, float(getattr(layer, "line_weight", default) or default))

    return default


def line_type_for(item):
    """Return the effective line type name for an entity."""

    layer = getattr(item, "layer", None)

    if layer is not None:
        return getattr(layer, "line_type", "Continuous")

    return "Continuous"


def hex_to_rgb(color):
    """Convert #RRGGBB to an RGB tuple."""

    value = str(color or "#e0e0e0").strip().lstrip("#")

    if len(value) != 6:
        value = "e0e0e0"

    try:
        return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))
    except ValueError:
        return (224, 224, 224)


def true_color(color):
    """Return a DXF true-color integer."""

    red, green, blue = hex_to_rgb(color)

    return red * 65536 + green * 256 + blue


def escape_text(value):
    """Escape text for XML/SVG output."""

    return html.escape(str(value or ""))


def points_attr(points):
    """Return SVG polygon point text."""

    return " ".join(f"{point.x:.3f},{point.y:.3f}" for point in points)


def arc_endpoint(center, radius, angle_degrees):
    """Return an arc endpoint from center, radius and degrees."""

    from engine.geometry import Vector2

    radians = math.radians(angle_degrees)

    return Vector2(
        center.x + math.cos(radians) * radius,
        center.y + math.sin(radians) * radius,
    )

