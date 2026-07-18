from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExportOptions:
    """Options shared by all CAD exporters."""

    page_width: float = 800.0
    page_height: float = 600.0
    margin: float = 24.0
    scale: float = 1.0
    image_width: int = 1600
    image_height: int = 1200
    dpi: int = 300
    transparent_background: bool = True
    background_color: str = "#FFFFFF"
    raster_scope: str = "entire_drawing"
    view_bounds: object = None
    include_hidden_layers: bool = False
    version: str = "0.8"


@dataclass
class ExportEntity:
    """Canonical export view of one workspace entity."""

    entity: object
    layer: object = None
    block_path: tuple = field(default_factory=tuple)


@dataclass
class ExportContext:
    """Canonical workspace export model consumed by all exporters."""

    workspace: object
    entities: list
    layers: list
    dimension_styles: list
    patterns: list
    blocks: list
    groups: list
    options: ExportOptions = field(default_factory=ExportOptions)

    @property
    def bounds(self):
        """Return current export bounds from collected entities."""

        if not self.entities:
            return None

        from engine.geometry import BoundingBox

        box = BoundingBox()

        for item in self.entities:
            entity_box = item.entity.bounding_box
            box.add(entity_box.min)
            box.add(entity_box.max)

        return box

    def target_path(self, path):
        """Normalize an export destination path."""

        return Path(path)
