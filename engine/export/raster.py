from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter

from engine.entities import BlockReference


class RasterExportRenderer:
    """Shared raster renderer for image-based exporters."""

    def __init__(self, context):

        self.context = context

    # --------------------------------

    def render(self, predicate=None, force_background=None):
        """Render selected export items into a QImage."""

        options = self.context.options
        image = QImage(
            int(options.image_width),
            int(options.image_height),
            QImage.Format_ARGB32_Premultiplied,
        )
        self._fill_background(image, force_background)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        self._apply_transform(painter)

        for item in self.context.entities:
            if predicate is not None and not predicate(item):
                continue

            if isinstance(item.entity, BlockReference):
                continue

            item.entity.draw(painter)

        painter.end()
        image.setDotsPerMeterX(self._dots_per_meter())
        image.setDotsPerMeterY(self._dots_per_meter())

        return image

    # --------------------------------

    def _fill_background(self, image, force_background):

        options = self.context.options

        if force_background is not None:
            image.fill(QColor(force_background))
            return

        if options.transparent_background:
            image.fill(Qt.transparent)
        else:
            image.fill(QColor(options.background_color))

    # --------------------------------

    def _apply_transform(self, painter):

        bounds = self._bounds()
        options = self.context.options

        if bounds is None:
            return

        margin = float(options.margin)
        usable_width = max(1.0, options.image_width - margin * 2.0)
        usable_height = max(1.0, options.image_height - margin * 2.0)
        scale = min(
            usable_width / max(1.0, bounds.width),
            usable_height / max(1.0, bounds.height),
        ) * float(options.scale)

        painter.translate(margin, options.image_height - margin)
        painter.scale(scale, -scale)
        painter.translate(-bounds.min.x, -bounds.min.y)

    # --------------------------------

    def _bounds(self):

        if self.context.options.raster_scope == "current_view":
            return self.context.options.view_bounds or self.context.bounds

        if self.context.options.raster_scope == "fit_to_page":
            return self.context.bounds

        return self.context.bounds

    # --------------------------------

    def _dots_per_meter(self):

        return int(float(self.context.options.dpi) / 0.0254)


def save_png(image, path):
    """Save a QImage as PNG."""

    target = str(path)
    image.save(target, "PNG")


def item_category(item):
    """Return the logical graphics-export layer for an export item."""

    from engine.entities import HatchEntity, LeaderEntity, MTextEntity, TextEntity

    entity = item.entity

    if item.block_path:
        return "Block Layer"

    if getattr(entity, "is_dimension", False):
        return "Dimension Layer"

    if isinstance(entity, HatchEntity):
        return "Hatch Layer"

    if isinstance(entity, (TextEntity, MTextEntity, LeaderEntity)):
        return "Annotation Layer"

    return "Drawing Layer"
