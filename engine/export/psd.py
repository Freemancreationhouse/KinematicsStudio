import struct

from PySide6.QtGui import QImage

from .base import Exporter
from .raster import RasterExportRenderer, item_category


class PSDExporter(Exporter):
    """Exports layered raster artwork in Photoshop PSD format."""

    extension = "psd"
    format_name = "PSD"
    LAYER_NAMES = [
        "Background Layer",
        "Drawing Layer",
        "Annotation Layer",
        "Dimension Layer",
        "Hatch Layer",
        "Block Layer",
    ]

    def export(self, context, path):
        """Write a layered PSD file and return the destination path."""

        target = context.target_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.serialize_bytes(context))

        return target

    def serialize(self, context):
        """PSD export is binary and is written through export()."""

        return ""

    # --------------------------------

    def serialize_bytes(self, context):
        """Return PSD bytes."""

        renderer = RasterExportRenderer(context)
        layers = self._layers(context, renderer)
        merged = renderer.render(force_background=context.options.background_color)
        width = int(context.options.image_width)
        height = int(context.options.image_height)

        return b"".join([
            self._header(width, height),
            struct.pack(">I", 0),
            struct.pack(">I", 0),
            self._layer_mask_section(layers, width, height),
            self._merged_image_data(merged, width, height),
        ])

    # --------------------------------

    def _layers(self, context, renderer):

        layers = []

        for name in self.LAYER_NAMES:
            if name == "Background Layer":
                image = renderer.render(lambda item: False, force_background=context.options.background_color)
            else:
                image = renderer.render(lambda item, target=name: item_category(item) == target, force_background=None)

            layers.append((name, image))

        return layers

    # --------------------------------

    def _header(self, width, height):

        return b"".join([
            b"8BPS",
            struct.pack(">H", 1),
            b"\0" * 6,
            struct.pack(">H", 4),
            struct.pack(">I", height),
            struct.pack(">I", width),
            struct.pack(">H", 8),
            struct.pack(">H", 3),
        ])

    # --------------------------------

    def _layer_mask_section(self, layers, width, height):

        records = bytearray()
        channel_data = bytearray()

        for name, image in layers:
            channels = self._channels(image, width, height)
            records.extend(self._layer_record(name, width, height, channels))

            for data in channels:
                channel_data.extend(struct.pack(">H", 0))
                channel_data.extend(data)

        layer_info = struct.pack(">Ih", len(records) + len(channel_data) + 2, len(layers))
        layer_info += bytes(records)
        layer_info += bytes(channel_data)
        section_body = layer_info + struct.pack(">I", 0)

        return struct.pack(">I", len(section_body)) + section_body

    # --------------------------------

    def _layer_record(self, name, width, height, channels):

        record = bytearray()
        record.extend(struct.pack(">iiii", 0, 0, height, width))
        record.extend(struct.pack(">H", 4))

        for channel_id, data in zip((0, 1, 2, -1), channels):
            record.extend(struct.pack(">hI", channel_id, len(data) + 2))

        record.extend(b"8BIM")
        record.extend(b"norm")
        record.extend(struct.pack(">BBBB", 255, 0, 8, 0))
        extra = struct.pack(">I", 0) + struct.pack(">I", 0) + self._pascal_name(name)
        record.extend(struct.pack(">I", len(extra)))
        record.extend(extra)

        return record

    # --------------------------------

    def _pascal_name(self, name):

        raw = str(name).encode("macroman", errors="replace")[:255]
        data = bytes([len(raw)]) + raw

        while len(data) % 4:
            data += b"\0"

        return data

    # --------------------------------

    def _channels(self, image, width, height):

        rgba = image.convertToFormat(QImage.Format_RGBA8888)
        red = bytearray()
        green = bytearray()
        blue = bytearray()
        alpha = bytearray()

        for y in range(height):
            for x in range(width):
                color = rgba.pixelColor(x, y)
                red.append(color.red())
                green.append(color.green())
                blue.append(color.blue())
                alpha.append(color.alpha())

        return [bytes(red), bytes(green), bytes(blue), bytes(alpha)]

    # --------------------------------

    def _merged_image_data(self, image, width, height):

        channels = self._channels(image, width, height)[:3]
        data = bytearray(struct.pack(">H", 0))

        for channel in channels:
            data.extend(channel)

        return bytes(data)
