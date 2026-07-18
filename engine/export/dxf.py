from engine.entities import (
    ArcEntity,
    BlockReference,
    CircleEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    MTextEntity,
    RectangleEntity,
    PolylineEntity,
    SplineEntity,
    TextEntity,
)

from .base import Exporter
from .helpers import color_for, layer_name, line_type_for, line_weight_for, true_color


class DXFExporter(Exporter):
    """Exports the canonical workspace model to ASCII DXF."""

    extension = "dxf"
    format_name = "DXF"

    def serialize(self, context):
        """Return an ASCII DXF document."""

        lines = []
        self._header(lines)
        self._tables(lines, context)
        self._entities(lines, context)
        lines.extend(["0", "EOF"])

        return "\n".join(lines) + "\n"

    # --------------------------------

    def _header(self, lines):

        lines.extend([
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER",
            "1", "AC1027",
            "0", "ENDSEC",
        ])

    # --------------------------------

    def _tables(self, lines, context):

        lines.extend(["0", "SECTION", "2", "TABLES"])
        lines.extend(["0", "TABLE", "2", "LTYPE", "70", "3"])

        for name in ("Continuous", "Dashed", "Center", "Hidden"):
            lines.extend(["0", "LTYPE", "2", name, "70", "0", "3", name, "72", "65", "73", "0", "40", "0.0"])

        lines.extend(["0", "ENDTAB", "0", "TABLE", "2", "LAYER", "70", str(len(context.layers))])

        for layer in context.layers:
            lines.extend([
                "0", "LAYER",
                "2", layer.name,
                "70", "0",
                "62", "7",
                "6", layer.line_type,
                "370", str(int(float(layer.line_weight) * 100)),
                "420", str(true_color(layer.color)),
            ])

        lines.extend(["0", "ENDTAB", "0", "ENDSEC"])

    # --------------------------------

    def _entities(self, lines, context):

        lines.extend(["0", "SECTION", "2", "ENTITIES"])

        for item in context.entities:
            self._entity(lines, item)

        lines.extend(["0", "ENDSEC"])

    # --------------------------------

    def _entity(self, lines, item):

        entity = item.entity

        if isinstance(entity, LineEntity):
            self._line(lines, item, entity.start, entity.end)
        elif isinstance(entity, RectangleEntity):
            self._rectangle(lines, item, entity)
        elif isinstance(entity, CircleEntity):
            self._circle(lines, item, entity)
        elif isinstance(entity, ArcEntity):
            self._arc(lines, item, entity)
        elif isinstance(entity, PolylineEntity):
            self._polyline(lines, item, entity.points, entity.closed)
        elif isinstance(entity, SplineEntity):
            self._polyline(lines, item, entity.sampled_points(), False)
        elif isinstance(entity, TextEntity):
            self._text(lines, item, entity.position, entity.text, entity.height, entity.rotation)
        elif isinstance(entity, MTextEntity):
            self._mtext(lines, item, entity)
        elif isinstance(entity, LeaderEntity):
            self._leader(lines, item, entity)
        elif isinstance(entity, HatchEntity):
            self._hatch(lines, item, entity)
        elif getattr(entity, "is_dimension", False):
            self._dimension(lines, item, entity)
        elif isinstance(entity, BlockReference):
            self._block_reference(lines, item, entity)

    # --------------------------------

    def _common(self, lines, item):

        lines.extend([
            "8", layer_name(item),
            "6", line_type_for(item),
            "370", str(int(line_weight_for(item) * 100)),
            "420", str(true_color(color_for(item))),
        ])

    # --------------------------------

    def _line(self, lines, item, start, end):

        lines.extend(["0", "LINE"])
        self._common(lines, item)
        lines.extend([
            "10", f"{start.x:.6f}",
            "20", f"{start.y:.6f}",
            "30", "0.0",
            "11", f"{end.x:.6f}",
            "21", f"{end.y:.6f}",
            "31", "0.0",
        ])

    # --------------------------------

    def _rectangle(self, lines, item, entity):

        left = min(entity.p1.x, entity.p2.x)
        right = max(entity.p1.x, entity.p2.x)
        top = min(entity.p1.y, entity.p2.y)
        bottom = max(entity.p1.y, entity.p2.y)
        points = [
            (left, top),
            (right, top),
            (right, bottom),
            (left, bottom),
        ]
        lines.extend(["0", "LWPOLYLINE"])
        self._common(lines, item)
        lines.extend(["90", "4", "70", "1"])

        for x, y in points:
            lines.extend(["10", f"{x:.6f}", "20", f"{y:.6f}"])

    # --------------------------------

    def _polyline(self, lines, item, points, closed=False):

        lines.extend(["0", "LWPOLYLINE"])
        self._common(lines, item)
        lines.extend(["90", str(len(points)), "70", "1" if closed else "0"])

        for point in points:
            lines.extend(["10", f"{point.x:.6f}", "20", f"{point.y:.6f}"])

    # --------------------------------

    def _circle(self, lines, item, entity):

        lines.extend(["0", "CIRCLE"])
        self._common(lines, item)
        lines.extend([
            "10", f"{entity.center.x:.6f}",
            "20", f"{entity.center.y:.6f}",
            "30", "0.0",
            "40", f"{entity.radius:.6f}",
        ])

    # --------------------------------

    def _arc(self, lines, item, entity):

        lines.extend(["0", "ARC"])
        self._common(lines, item)
        lines.extend([
            "10", f"{entity.center.x:.6f}",
            "20", f"{entity.center.y:.6f}",
            "30", "0.0",
            "40", f"{entity.radius:.6f}",
            "50", f"{entity.start_angle:.6f}",
            "51", f"{entity.end_angle:.6f}",
        ])

    # --------------------------------

    def _text(self, lines, item, position, text, height, rotation=0.0):

        lines.extend(["0", "TEXT"])
        self._common(lines, item)
        lines.extend([
            "10", f"{position.x:.6f}",
            "20", f"{position.y:.6f}",
            "30", "0.0",
            "40", f"{float(height):.6f}",
            "1", str(text or ""),
            "50", f"{float(rotation):.6f}",
        ])

    # --------------------------------

    def _mtext(self, lines, item, entity):

        lines.extend(["0", "MTEXT"])
        self._common(lines, item)
        lines.extend([
            "10", f"{entity.position.x:.6f}",
            "20", f"{entity.position.y:.6f}",
            "30", "0.0",
            "40", f"{entity.height:.6f}",
            "41", f"{entity.box_width:.6f}",
            "1", str(entity.text or ""),
            "50", f"{entity.rotation:.6f}",
        ])

    # --------------------------------

    def _leader(self, lines, item, entity):

        self._line(lines, item, entity.arrow_point, entity.landing_start)
        self._line(lines, item, entity.landing_start, entity.landing_end)
        self._text(
            lines,
            item,
            entity.text_entity.position,
            entity.text_entity.text,
            entity.text_entity.height,
            entity.text_entity.rotation,
        )

    # --------------------------------

    def _dimension(self, lines, item, entity):

        for start, end in entity.segments():
            self._line(lines, item, start, end)

        style = entity.effective_style()
        self._text(lines, item, entity.text_position(style), entity.formatted_measurement(), style.text_height)

    # --------------------------------

    def _hatch(self, lines, item, entity):

        points = entity.current_boundary_points()

        if len(points) < 3:
            return

        lines.extend(["0", "HATCH"])
        self._common(lines, item)
        lines.extend([
            "10", "0.0",
            "20", "0.0",
            "30", "0.0",
            "2", entity.pattern_name,
            "70", "1" if entity.pattern_name.upper() == "SOLID" else "0",
            "71", "0",
            "91", "1",
            "92", "2",
            "72", "1",
            "73", "1",
            "93", str(len(points)),
        ])

        for point in points:
            lines.extend(["10", f"{point.x:.6f}", "20", f"{point.y:.6f}"])

        lines.extend(["97", "0"])

    # --------------------------------

    def _block_reference(self, lines, item, entity):

        if entity.definition_name is None:
            return

        lines.extend(["0", "INSERT"])
        self._common(lines, item)
        lines.extend([
            "2", entity.definition_name,
            "10", f"{entity.insertion_point.x:.6f}",
            "20", f"{entity.insertion_point.y:.6f}",
            "30", "0.0",
            "41", f"{entity.scale_x:.6f}",
            "42", f"{entity.scale_y:.6f}",
            "50", f"{entity.rotation:.6f}",
        ])
