from .base import Exporter
from .raster import RasterExportRenderer, save_png


class PNGExporter(Exporter):
    """Exports the canonical workspace model to high-quality PNG."""

    extension = "png"
    format_name = "PNG"

    def export(self, context, path):
        """Write a PNG image and return the destination path."""

        target = context.target_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image = RasterExportRenderer(context).render()
        save_png(image, target)

        return target

    def serialize(self, context):
        """PNG export is binary and is written through export()."""

        return ""
