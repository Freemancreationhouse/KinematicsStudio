import tempfile
from pathlib import Path

from engine.cad.application import CADApplication
from engine.entities import (
    AlignedDimensionEntity,
    ArcEntity,
    BlockReference,
    CircleEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    MTextEntity,
    RectangleEntity,
    TextEntity,
)
from engine.geometry import Vector2


app = CADApplication()
workspace = app.workspace
export_layer = workspace.create_layer("Export", "#FFAA00", "Dashed", 0.35)
workspace.set_current_layer(export_layer)

line = LineEntity(Vector2(0, 0), Vector2(100, 0))
rectangle = RectangleEntity(Vector2(10, 10), Vector2(80, 60))
circle = CircleEntity(Vector2(140, 40), 25)
arc = ArcEntity(Vector2(200, 40), 30, 0, 120)
text = TextEntity(Vector2(0, 90), "Export Text", 10)
mtext = MTextEntity(Vector2(0, 110), "Multi line export text", 120, 50, 8)
leader = LeaderEntity(Vector2(180, 90), Vector2(210, 110), Vector2(260, 110))
dimension = AlignedDimensionEntity(Vector2(0, 0), Vector2(100, 0), Vector2(0, 25))

for entity in (line, rectangle, circle, arc, text, mtext, leader, dimension):
    workspace.add_entity(entity)

hatch = HatchEntity(boundary_entities=[rectangle], pattern_name="SOLID")
workspace.add_entity(hatch)

definition = workspace.block_manager.create_definition(
    "ExportBlock",
    origin=Vector2(0, 0),
    entities=[LineEntity(Vector2(0, 0), Vector2(20, 20)), CircleEntity(Vector2(15, 15), 5)],
)
reference = BlockReference(definition, Vector2(260, 30))
workspace.add_entity(reference)
workspace.group_manager.create("ExportGroup", [line, rectangle])

context = app.export_manager.context(workspace)
assert len(context.layers) >= 2
assert len(context.blocks) == 1
assert len(context.groups) == 1
assert len(context.entities) > len(workspace.entities)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    dxf = app.export_project(root / "drawing.dxf", "dxf")
    svg = app.export_project(root / "drawing.svg", "svg")
    pdf = app.export_project(root / "drawing.pdf", "pdf")

    dxf_text = dxf.read_text(encoding="utf-8")
    svg_text = svg.read_text(encoding="utf-8")
    pdf_bytes = pdf.read_bytes()

    assert "SECTION" in dxf_text
    assert "LAYER" in dxf_text
    assert "LINE" in dxf_text
    assert "CIRCLE" in dxf_text
    assert "HATCH" in dxf_text
    assert "INSERT" in dxf_text
    assert "Export Text" in dxf_text

    assert "<svg" in svg_text
    assert "layer-Export" in svg_text
    assert "<line" in svg_text
    assert "<circle" in svg_text
    assert "<polygon" in svg_text
    assert "Export Text" in svg_text

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes

print("cad-export-ok")
