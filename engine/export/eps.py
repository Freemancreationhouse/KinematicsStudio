from engine.entities import (
    ArcEntity,
    BlockReference,
    CircleEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    MTextEntity,
    PolylineEntity,
    RectangleEntity,
    SplineEntity,
    TextEntity,
)

from .base import Exporter
from .helpers import color_for, hex_to_rgb


class EPSExporter(Exporter):
    """Exports the canonical workspace model to vector EPS."""

    extension = "eps"
    format_name = "EPS"

    def serialize(self, context):
        """Return Encapsulated PostScript content."""

        bounds = context.bounds
        width = int(context.options.page_width)
        height = int(context.options.page_height)
        lines = [
            "%!PS-Adobe-3.0 EPSF-3.0",
            f"%%BoundingBox: 0 0 {width} {height}",
            "%%Creator: Kinematics Studio V2",
            "%%EndComments",
            "/F1 /Helvetica findfont def",
            "gsave",
        ]
        mapper = _EPSMapper(context)

        for item in context.entities:
            lines.extend(self._entity(item, mapper))

        lines.extend(["grestore", "showpage", "%%EOF"])

        return "\n".join(lines) + "\n"

    # --------------------------------

    def _entity(self, item, mapper):

        entity = item.entity

        if isinstance(entity, LineEntity):
            return self._line(item, mapper, entity.start, entity.end)
        if isinstance(entity, RectangleEntity):
            return self._rectangle(item, mapper, entity)
        if isinstance(entity, CircleEntity):
            return self._circle(item, mapper, entity)
        if isinstance(entity, ArcEntity):
            return self._arc(item, mapper, entity)
        if isinstance(entity, PolylineEntity):
            return self._polyline(item, mapper, entity.points, entity.closed)
        if isinstance(entity, SplineEntity):
            return self._polyline(item, mapper, entity.sampled_points(), False)
        if isinstance(entity, TextEntity):
            return self._text(item, mapper, entity.position, entity.text, entity.height)
        if isinstance(entity, MTextEntity):
            return self._mtext(item, mapper, entity)
        if isinstance(entity, LeaderEntity):
            return self._leader(item, mapper, entity)
        if isinstance(entity, HatchEntity):
            return self._hatch(item, mapper, entity)
        if getattr(entity, "is_dimension", False):
            return self._dimension(item, mapper, entity)
        if isinstance(entity, BlockReference):
            return []

        return []

    # --------------------------------

    def _style(self, item):

        red, green, blue = [value / 255.0 for value in hex_to_rgb(color_for(item))]
        layer = getattr(item, "layer", None)
        weight = max(0.1, float(getattr(layer, "line_weight", 1.0) or 1.0))

        return [f"{red:.4f} {green:.4f} {blue:.4f} setrgbcolor", f"{weight:.3f} setlinewidth"]

    # --------------------------------

    def _line(self, item, mapper, start, end):

        x1, y1 = mapper.point(start)
        x2, y2 = mapper.point(end)

        return self._style(item) + [f"newpath {x1:.3f} {y1:.3f} moveto {x2:.3f} {y2:.3f} lineto stroke"]

    # --------------------------------

    def _rectangle(self, item, mapper, entity):

        left = min(entity.p1.x, entity.p2.x)
        top = min(entity.p1.y, entity.p2.y)
        right = max(entity.p1.x, entity.p2.x)
        bottom = max(entity.p1.y, entity.p2.y)
        x1, y1 = mapper.xy(left, top)
        x2, y2 = mapper.xy(right, bottom)

        return self._style(item) + [
            f"newpath {x1:.3f} {y1:.3f} moveto {x2:.3f} {y1:.3f} lineto {x2:.3f} {y2:.3f} lineto {x1:.3f} {y2:.3f} lineto closepath stroke"
        ]

    # --------------------------------

    def _circle(self, item, mapper, entity):

        x, y = mapper.point(entity.center)
        radius = entity.radius * mapper.scale

        return self._style(item) + [f"newpath {x:.3f} {y:.3f} {radius:.3f} 0 360 arc stroke"]

    # --------------------------------

    def _polyline(self, item, mapper, points, closed=False):

        if len(points) < 2:
            return []

        commands = self._style(item)
        first_x, first_y = mapper.point(points[0])
        commands.append(f"newpath {first_x:.3f} {first_y:.3f} moveto")

        for point in points[1:]:
            x, y = mapper.point(point)
            commands.append(f"{x:.3f} {y:.3f} lineto")

        commands.append("closepath stroke" if closed else "stroke")

        return commands

    # --------------------------------

    def _arc(self, item, mapper, entity):

        x, y = mapper.point(entity.center)
        radius = entity.radius * mapper.scale

        return self._style(item) + [
            f"newpath {x:.3f} {y:.3f} {radius:.3f} {entity.start_angle:.3f} {entity.end_angle:.3f} arc stroke"
        ]

    # --------------------------------

    def _text(self, item, mapper, position, text, height):

        x, y = mapper.point(position)
        size = max(1.0, float(height) * mapper.scale)
        safe = self._ps_text(text)

        return self._style(item) + [
            f"F1 {size:.3f} scalefont setfont",
            f"{x:.3f} {y:.3f} moveto ({safe}) show",
        ]

    # --------------------------------

    def _mtext(self, item, mapper, entity):

        lines = []
        y = entity.position.y

        for text in entity.lines():
            y += entity.height
            point = type("Point", (), {"x": entity.position.x, "y": y})()
            lines.extend(self._text(item, mapper, point, text, entity.height))

        return lines

    # --------------------------------

    def _leader(self, item, mapper, entity):

        lines = []
        lines.extend(self._line(item, mapper, entity.arrow_point, entity.landing_start))
        lines.extend(self._line(item, mapper, entity.landing_start, entity.landing_end))
        lines.extend(self._text(item, mapper, entity.text_entity.position, entity.text_entity.text, entity.text_entity.height))

        return lines

    # --------------------------------

    def _dimension(self, item, mapper, entity):

        lines = []

        for start, end in entity.segments():
            lines.extend(self._line(item, mapper, start, end))

        style = entity.effective_style()
        lines.extend(self._text(item, mapper, entity.text_position(style), entity.formatted_measurement(), style.text_height))

        return lines

    # --------------------------------

    def _hatch(self, item, mapper, entity):

        points = entity.current_boundary_points()

        if len(points) < 3:
            return []

        commands = self._style(item)
        first_x, first_y = mapper.point(points[0])
        commands.append(f"newpath {first_x:.3f} {first_y:.3f} moveto")

        for point in points[1:]:
            x, y = mapper.point(point)
            commands.append(f"{x:.3f} {y:.3f} lineto")

        commands.append("closepath gsave 0.25 setgray fill grestore stroke")

        return commands

    # --------------------------------

    def _ps_text(self, value):

        return str(value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class _EPSMapper:
    """Maps workspace coordinates into EPS page space."""

    def __init__(self, context):

        self.context = context
        self.bounds = context.bounds
        self.scale = self._scale()

    # --------------------------------

    def point(self, point):

        return self.xy(point.x, point.y)

    # --------------------------------

    def xy(self, x, y):

        options = self.context.options

        if self.bounds is None:
            return x, options.page_height - y

        px = options.margin + (x - self.bounds.min.x) * self.scale
        py = options.page_height - options.margin - (y - self.bounds.min.y) * self.scale

        return px, py

    # --------------------------------

    def _scale(self):

        options = self.context.options
        bounds = self.bounds

        if bounds is None:
            return options.scale

        usable_width = max(1.0, options.page_width - options.margin * 2.0)
        usable_height = max(1.0, options.page_height - options.margin * 2.0)

        return min(
            usable_width / max(1.0, bounds.width),
            usable_height / max(1.0, bounds.height),
        ) * options.scale
