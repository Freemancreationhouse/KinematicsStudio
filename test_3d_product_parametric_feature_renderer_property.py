import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ExtrudeFeature, FeatureDefinition, FeatureOptions, ProductPart, Sketch, SolidBody
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Parametric Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Parametric Product")
part = manager.add_part(ProductPart("Rendered Parametric Part", "Rendered Parametric Mesh"))
sketch = manager.add_sketch_item(Sketch("Rendered Parametric Sketch", part.id))
body = manager.add_body_item(SolidBody("Rendered Parametric Body", part.id, "Rendered Parametric Mesh"))
feature = manager.add_feature_item(
    ExtrudeFeature(
        "Rendered Parametric Extrude",
        part.id,
        FeatureDefinition(sketch.id, "", body.id, [body.id], FeatureOptions("Join", distance=5.0)),
    )
)
manager.dependency_manager.add_edge(sketch, feature, "SketchToFeature")
manager.feature_editor.edit_feature(feature, distance=14.0)
workspace.selection.select(feature)

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
panel.show_selection([feature])

assert panel.type.text() == "ExtrudeFeature"
assert "Distance: 14.00" in panel.length.text()
assert panel.line_weight.text() == "Dirty"
assert "Dependencies: 1" in panel.height.text()

manager.regeneration_manager.rebuild_feature(feature, workspace)
panel.show_selection([feature])
assert panel.line_weight.text() == "Active"
assert "Result: Applied" in panel.height.text() or "Result: Rebuilt" in panel.height.text()

print("3d-product-parametric-feature-renderer-property-ok")
