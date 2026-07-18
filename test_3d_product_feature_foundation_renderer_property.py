import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ExtrudeFeature, FeatureDefinition, FeatureOptions, ProductPart, SolidBody
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Rendered Body Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Feature Product", "mm", 3)
part = manager.add_part(ProductPart("Rendered Feature Part", "Rendered Body Mesh"))
body = manager.add_body_item(SolidBody("Rendered Body", part.id, "Rendered Body Mesh"))
feature = manager.add_feature_item(
    ExtrudeFeature(
        "Rendered Extrude",
        part.id,
        FeatureDefinition(body_id=body.id, target_body_ids=[body.id], options=FeatureOptions("Cut", distance=6.0)),
    )
)
manager.feature_manager.apply_feature(feature, workspace)
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

panel.show_selection([part])
assert "Bodies: 1" in panel.radius.text()
assert "Features: 1" in panel.radius.text()

panel.show_selection([body])
assert panel.type.text() == "SolidBody"
assert "Features: 1" in panel.radius.text()
assert "Mesh: Rendered Body Mesh" in panel.line_type.text()

panel.show_selection([feature])
assert panel.type.text() == "ExtrudeFeature"
assert "Type: Extrude" in panel.radius.text()
assert "Distance: 6.00" in panel.length.text()
assert "Operation: Cut" in panel.line_type.text()
assert "Result: Applied" in panel.height.text()

print("3d-product-feature-foundation-renderer-property-ok")
