import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane, SketchProfile
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])
workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Rendered Feature Framework", "mm", 3)
part = manager.add_part(ProductPart("Rendered Feature Part", "rendered-feature-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Rendered Feature Plane"))
sketch = manager.sketch_manager.create_sketch("Rendered Feature Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Rendered Feature Line", sketch.id, Vector3(), Vector3(6.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Rendered Feature Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Extrude", part, profile, None, name="Rendered Extrude")
session = manager.feature_manager.create_execution_session(feature)
manager.feature_manager.execute_feature_metadata(feature, session)

renderer = Renderer3D()
for item in (feature, session):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (feature, session):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert feature in workspace.visible_product_objects()
assert session in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 0
assert len(manager.bodies) == 0
assert part.mesh_entity_id == "rendered-feature-mesh"

print("3d-parametric-feature-framework-renderer-property-ok")
