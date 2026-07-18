import zlib

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


class PDFExporter(Exporter):
    """Exports the canonical workspace model to a simple vector PDF."""

    extension = "pdf"
    format_name = "PDF"

    def export(self, context, path):
        """Write a binary PDF export and return the destination path."""

        target = context.target_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.serialize_bytes(context))

        return target

    def serialize(self, context):
        """Return a Latin-1 PDF string for compatibility with Exporter."""

        return self.serialize_bytes(context).decode("latin-1")

    # --------------------------------

    def serialize_bytes(self, context):
        """Return PDF bytes."""

        stream = self._content_stream(context)
        compressed = zlib.compress(stream.encode("latin-1", errors="replace"))
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            self._page_object(context),
            b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(compressed) + compressed + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]

        return self._pdf(objects)

    # --------------------------------

    def _page_object(self, context):

        width = context.options.page_width
        height = context.options.page_height

        return (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.3f} {height:.3f}] "
            f"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ).encode("latin-1")

    # --------------------------------

    def _content_stream(self, context):

        mapper = _PDFMapper(context)
        commands = ["q"]

        for item in context.entities:
            commands.extend(self._entity(item, mapper))

        commands.append("Q")

        return "\n".join(commands) + "\n"

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
            return self._circle(item, mapper, entity)
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

    def _stroke(self, item):

        red, green, blue = [value / 255.0 for value in hex_to_rgb(color_for(item))]
        weight = max(0.1, float(getattr(getattr(item, "layer", None), "line_weight", 1.0) or 1.0))

        return [f"{red:.4f} {green:.4f} {blue:.4f} RG", f"{weight:.3f} w"]

    # --------------------------------

    def _fill(self, item):

        red, green, blue = [value / 255.0 for value in hex_to_rgb(color_for(item))]

        return f"{red:.4f} {green:.4f} {blue:.4f} rg"

    # --------------------------------

    def _line(self, item, mapper, start, end):

        x1, y1 = mapper.point(start)
        x2, y2 = mapper.point(end)

        return self._stroke(item) + [f"{x1:.3f} {y1:.3f} m {x2:.3f} {y2:.3f} l S"]

    # --------------------------------

    def _rectangle(self, item, mapper, entity):

        left = min(entity.p1.x, entity.p2.x)
        top = min(entity.p1.y, entity.p2.y)
        right = max(entity.p1.x, entity.p2.x)
        bottom = max(entity.p1.y, entity.p2.y)
        x1, y1 = mapper.xy(left, top)
        x2, y2 = mapper.xy(right, bottom)

        return self._stroke(item) + [
            f"{x1:.3f} {y1:.3f} {x2 - x1:.3f} {y2 - y1:.3f} re S"
        ]

    # --------------------------------

    def _circle(self, item, mapper, entity):

        cx, cy = mapper.point(entity.center)
        radius = abs(entity.radius * mapper.scale)
        c = radius * 0.5522847498

        return self._stroke(item) + [
            f"{cx + radius:.3f} {cy:.3f} m",
            f"{cx + radius:.3f} {cy + c:.3f} {cx + c:.3f} {cy + radius:.3f} {cx:.3f} {cy + radius:.3f} c",
            f"{cx - c:.3f} {cy + radius:.3f} {cx - radius:.3f} {cy + c:.3f} {cx - radius:.3f} {cy:.3f} c",
            f"{cx - radius:.3f} {cy - c:.3f} {cx - c:.3f} {cy - radius:.3f} {cx:.3f} {cy - radius:.3f} c",
            f"{cx + c:.3f} {cy - radius:.3f} {cx + radius:.3f} {cy - c:.3f} {cx + radius:.3f} {cy:.3f} c S",
        ]

    # --------------------------------

    def _polyline(self, item, mapper, points, closed=False):

        if len(points) < 2:
            return []

        commands = self._stroke(item)
        first_x, first_y = mapper.point(points[0])
        commands.append(f"{first_x:.3f} {first_y:.3f} m")

        for point in points[1:]:
            x, y = mapper.point(point)
            commands.append(f"{x:.3f} {y:.3f} l")

        commands.append("h S" if closed else "S")

        return commands

    # --------------------------------

    def _text(self, item, mapper, position, text, height):

        x, y = mapper.point(position)
        size = max(1.0, float(height) * mapper.scale)
        safe = self._pdf_text(text)

        return [
            self._fill(item),
            "BT",
            f"/F1 {size:.3f} Tf",
            f"{x:.3f} {y:.3f} Td",
            f"({safe}) Tj",
            "ET",
        ]

    # --------------------------------

    def _mtext(self, item, mapper, entity):

        commands = []
        y = entity.position.y

        for line in entity.lines():
            y += entity.height
            point = type("Point", (), {"x": entity.position.x, "y": y})()
            commands.extend(self._text(item, mapper, point, line, entity.height))

        return commands

    # --------------------------------

    def _leader(self, item, mapper, entity):

        commands = []
        commands.extend(self._line(item, mapper, entity.arrow_point, entity.landing_start))
        commands.extend(self._line(item, mapper, entity.landing_start, entity.landing_end))
        commands.extend(self._text(item, mapper, entity.text_entity.position, entity.text_entity.text, entity.text_entity.height))

        return commands

    # --------------------------------

    def _dimension(self, item, mapper, entity):

        commands = []

        for start, end in entity.segments():
            commands.extend(self._line(item, mapper, start, end))

        style = entity.effective_style()
        commands.extend(self._text(item, mapper, entity.text_position(style), entity.formatted_measurement(), style.text_height))

        return commands

    # --------------------------------

    def _hatch(self, item, mapper, entity):

        points = entity.current_boundary_points()

        if len(points) < 3:
            return []

        commands = [self._fill(item), self._stroke(item)[0]]
        first_x, first_y = mapper.point(points[0])
        commands.append(f"{first_x:.3f} {first_y:.3f} m")

        for point in points[1:]:
            x, y = mapper.point(point)
            commands.append(f"{x:.3f} {y:.3f} l")

        commands.append("h B")

        return commands

    # --------------------------------

    def _pdf_text(self, text):

        return str(text or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # --------------------------------

    def _pdf(self, objects):

        result = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]

        for index, obj in enumerate(objects, start=1):
            offsets.append(len(result))
            result.extend(f"{index} 0 obj\n".encode("latin-1"))
            result.extend(obj)
            result.extend(b"\nendobj\n")

        xref = len(result)
        result.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        result.extend(b"0000000000 65535 f \n")

        for offset in offsets[1:]:
            result.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

        result.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
                f"startxref\n{xref}\n%%EOF\n"
            ).encode("latin-1")
        )

        return bytes(result)


class _PDFMapper:
    """Maps workspace coordinates into a PDF page."""

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
        bounds_width = max(1.0, bounds.width)
        bounds_height = max(1.0, bounds.height)

        return min(usable_width / bounds_width, usable_height / bounds_height) * options.scale
