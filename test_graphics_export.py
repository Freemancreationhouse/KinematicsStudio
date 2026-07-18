import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import (
    AlignedDimensionEntity,
    BlockReference,
    CircleEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    MTextEntity,
    RectangleEntity,
    TextEntity,
)
from engine.export import ExportOptions
from engine.geometry import Vector2


qt_app = QApplication.instance() or QApplication([])
app = CADApplication()
workspace = app.workspace
layer = workspace.create_layer("Graphics", "#00AAFF", "Continuous", 0.5)
workspace.set_current_layer(layer)

line = LineEntity(Vector2(0, 0), Vector2(100, 0))
rectangle = RectangleEntity(Vector2(10, 10), Vector2(90, 60))
circle = CircleEntity(Vector2(140, 40), 20)
text = TextEntity(Vector2(0, 90), "Graphics Text", 10)
mtext = MTextEntity(Vector2(0, 110), "Wrapped graphics text", 120, 40, 8)
leader = LeaderEntity(Vector2(180, 90), Vector2(210, 110), Vector2(250, 110))
dimension = AlignedDimensionEntity(Vector2(0, 0), Vector2(100, 0), Vector2(0, 25))

for entity in (line, rectangle, circle, text, mtext, leader, dimension):
    workspace.add_entity(entity)

hatch = HatchEntity(boundary_entities=[rectangle], pattern_name="SOLID")
workspace.add_entity(hatch)

definition = workspace.block_manager.create_definition(
    "GraphicsBlock",
    origin=Vector2(0, 0),
    entities=[LineEntity(Vector2(0, 0), Vector2(20, 20))],
)
workspace.add_entity(BlockReference(definition, Vector2(220, 30)))

options = ExportOptions(
    image_width=320,
    image_height=240,
    dpi=300,
    transparent_background=True,
)
white_options = ExportOptions(
    image_width=320,
    image_height=240,
    dpi=150,
    transparent_background=False,
    background_color="#FFFFFF",
)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    transparent_png = app.export_project(root / "transparent.png", "png", options)
    white_png = app.export_project(root / "white.png", "png", white_options)
    eps = app.export_project(root / "drawing.eps", "eps", options)
    psd = app.export_project(root / "drawing.psd", "psd", options)

    transparent_image = QImage(str(transparent_png))
    white_image = QImage(str(white_png))

    assert transparent_image.width() == 320
    assert transparent_image.height() == 240
    assert white_image.width() == 320
    assert white_image.height() == 240
    assert transparent_image.pixelColor(0, 0).alpha() == 0
    assert white_image.pixelColor(0, 0).alpha() == 255

    eps_text = eps.read_text(encoding="utf-8")
    assert eps_text.startswith("%!PS-Adobe-3.0 EPSF-3.0")
    assert "Graphics Text" in eps_text
    assert "setrgbcolor" in eps_text
    assert "arc stroke" in eps_text

    psd_bytes = psd.read_bytes()
    assert psd_bytes.startswith(b"8BPS")
    assert b"Background Layer" in psd_bytes
    assert b"Drawing Layer" in psd_bytes
    assert b"Annotation Layer" in psd_bytes
    assert b"Dimension Layer" in psd_bytes
    assert b"Hatch Layer" in psd_bytes
    assert b"Block Layer" in psd_bytes

print("graphics-export-ok")
