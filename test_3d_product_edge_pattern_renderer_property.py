import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import PatternDefinition, ProductPart, SolidBody
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(5.0, 5.0, 5.0), name="Rendered Edge Pattern Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Edge Pattern Product")
part = manager.add_part(ProductPart("Rendered Edge Pattern Part", "Rendered Edge Pattern Mesh"))
body = manager.add_body_item(SolidBody("Rendered Edge Pattern Body", part.id, "Rendered Edge Pattern Mesh"))
fillet = manager.edge_modification_manager.create_fillet(part, body, [0, 1], 2.0)
chamfer = manager.edge_modification_manager.create_chamfer(part, body, [2], 1.0)
pattern = manager.pattern_manager.create_pattern(
    part,
    body,
    source_features=[fillet, chamfer],
    pattern_definition=PatternDefinition("Linear Pattern", [fillet.id, chamfer.id], [], 4.0, 2),
)
workspace.selection.select(fillet)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)
image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.set_workspace(workspace)

panel.show_selection([fillet])
assert panel.type.text() == "FilletFeature"
assert "Fillet Radius" in panel.radius.text()
assert "Edges: 2" in panel.width.text()

panel.show_selection([chamfer])
assert panel.type.text() == "ChamferFeature"
assert "Chamfer Distance" in panel.radius.text()
assert "Edges: 1" in panel.width.text()

panel.show_selection([pattern])
assert panel.type.text() == "PatternFeature"
assert "Pattern: Linear Pattern" in panel.radius.text()
assert "Instances: 4" in panel.width.text()
assert "Count: 2" in panel.diameter.text()

print("3d-product-edge-pattern-renderer-property-ok")
