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
from .helpers import arc_endpoint, color_for, escape_text, layer_name, line_weight_for, points_attr


class SVGExporter(Exporter):
    """Exports the canonical workspace model to scalable vector SVG."""

    extension = "svg"
    format_name = "SVG"

    def serialize(self, context):
        """Return SVG markup."""

        view_box = self._view_box(context)
        elements = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="{view_box}">',
            '<g id="KinematicsStudioExport">',
        ]

        current_layer = None

        for item in context.entities:
            name = layer_name(item)

            if name != current_layer:
                if current_layer is not None:
                    elements.append("</g>")

                elements.append(f'<g id="layer-{escape_text(name)}">')
                current_layer = name

            elements.extend(self._entity(item))

        if current_layer is not None:
            elements.append("</g>")

        elements.extend(["</g>", "</svg>"])

        return "\n".join(elements) + "\n"

    # --------------------------------

    def _view_box(self, context):

        bounds = context.bounds

        if bounds is None:
            return "0 0 800 600"

        margin = context.options.margin
        width = max(1.0, bounds.width + margin * 2.0)
        height = max(1.0, bounds.height + margin * 2.0)

        return f"{bounds.min.x - margin:.3f} {bounds.min.y - margin:.3f} {width:.3f} {height:.3f}"

    # --------------------------------

    def _entity(self, item):

        entity = item.entity

        if isinstance(entity, LineEntity):
            return [self._line(item, entity.start, entity.end)]
        if isinstance(entity, RectangleEntity):
            return [self._rectangle(item, entity)]
        if isinstance(entity, CircleEntity):
            return [self._circle(item, entity)]
        if isinstance(entity, ArcEntity):
            return [self._arc(item, entity)]
        if isinstance(entity, PolylineEntity):
            return [self._polyline(item, entity.points, entity.closed)]
        if isinstance(entity, SplineEntity):
            return [self._polyline(item, entity.sampled_points(), False)]
        if isinstance(entity, TextEntity):
            return [self._text(item, entity.position, entity.text, entity.height, entity.rotation)]
        if isinstance(entity, MTextEntity):
            return self._mtext(item, entity)
        if isinstance(entity, LeaderEntity):
            return self._leader(item, entity)
        if isinstance(entity, HatchEntity):
            return [self._hatch(item, entity)]
        if getattr(entity, "is_dimension", False):
            return self._dimension(item, entity)
        if isinstance(entity, BlockReference):
            return [self._block_reference(item, entity)]

        return []

    # --------------------------------

    def _style(self, item, fill="none"):

        return (
            f'stroke="{color_for(item)}" '
            f'stroke-width="{line_weight_for(item):.3f}" '
            f'fill="{fill}" vector-effect="non-scaling-stroke"'
        )

    # --------------------------------

    def _line(self, item, start, end):

        return (
            f'<line x1="{start.x:.3f}" y1="{start.y:.3f}" '
            f'x2="{end.x:.3f}" y2="{end.y:.3f}" {self._style(item)} />'
        )

    # --------------------------------

    def _rectangle(self, item, entity):

        left = min(entity.p1.x, entity.p2.x)
        top = min(entity.p1.y, entity.p2.y)

        return (
            f'<rect x="{left:.3f}" y="{top:.3f}" width="{entity.width:.3f}" '
            f'height="{entity.height:.3f}" {self._style(item)} />'
        )

    # --------------------------------

    def _circle(self, item, entity):

        return (
            f'<circle cx="{entity.center.x:.3f}" cy="{entity.center.y:.3f}" '
            f'r="{entity.radius:.3f}" {self._style(item)} />'
        )

    # --------------------------------

    def _polyline(self, item, points, closed=False):

        tag = "polygon" if closed else "polyline"

        return f'<{tag} points="{points_attr(points)}" {self._style(item)} />'

    # --------------------------------

    def _arc(self, item, entity):

        start = arc_endpoint(entity.center, entity.radius, entity.start_angle)
        end = arc_endpoint(entity.center, entity.radius, entity.end_angle)
        span = abs(entity.end_angle - entity.start_angle)
        large = "1" if span > 180.0 else "0"

        return (
            f'<path d="M {start.x:.3f} {start.y:.3f} '
            f'A {entity.radius:.3f} {entity.radius:.3f} 0 {large} 1 {end.x:.3f} {end.y:.3f}" '
            f'{self._style(item)} />'
        )

    # --------------------------------

    def _text(self, item, position, text, height, rotation=0.0):

        transform = f' transform="rotate({float(rotation):.3f} {position.x:.3f} {position.y:.3f})"' if rotation else ""

        return (
            f'<text x="{position.x:.3f}" y="{position.y:.3f}" '
            f'font-size="{float(height):.3f}" fill="{color_for(item)}"{transform}>'
            f'{escape_text(text)}</text>'
        )

    # --------------------------------

    def _mtext(self, item, entity):

        elements = []
        y = entity.position.y

        for line in entity.lines():
            y += entity.height
            elements.append(self._text(item, type("Point", (), {"x": entity.position.x, "y": y})(), line, entity.height, entity.rotation))

        return elements

    # --------------------------------

    def _leader(self, item, entity):

        return [
            self._line(item, entity.arrow_point, entity.landing_start),
            self._line(item, entity.landing_start, entity.landing_end),
            self._text(item, entity.text_entity.position, entity.text_entity.text, entity.text_entity.height, entity.text_entity.rotation),
        ]

    # --------------------------------

    def _dimension(self, item, entity):

        elements = [
            self._line(item, start, end)
            for start, end in entity.segments()
        ]
        style = entity.effective_style()
        elements.append(
            self._text(item, entity.text_position(style), entity.formatted_measurement(), style.text_height)
        )

        return elements

    # --------------------------------

    def _hatch(self, item, entity):

        points = entity.current_boundary_points()

        if len(points) < 3:
            return ""

        fill = color_for(item) if entity.pattern_name.upper() == "SOLID" else "none"

        return (
            f'<polygon points="{points_attr(points)}" {self._style(item, fill)} '
            f'fill-opacity="0.25" />'
        )

    # --------------------------------

    def _block_reference(self, item, entity):

        return (
            f'<g data-block="{escape_text(entity.definition_name)}" '
            f'transform="translate({entity.insertion_point.x:.3f} {entity.insertion_point.y:.3f}) '
            f'rotate({entity.rotation:.3f}) scale({entity.scale_x:.3f} {entity.scale_y:.3f})" />'
        )
