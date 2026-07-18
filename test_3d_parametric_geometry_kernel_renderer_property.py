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
manager.create_document("Rendered Geometry Kernel", "mm", 3)
part = manager.add_part(ProductPart("Rendered Kernel Part", "rendered-kernel-part", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Rendered Kernel Plane"))
sketch = manager.sketch_manager.create_sketch("Rendered Kernel Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Rendered Kernel Line", sketch.id, Vector3(), Vector3(6.0, 0.0, 0.0)))
profile = manager.add_sketch_item(SketchProfile("Rendered Kernel Profile", sketch.id, [line.id]))
feature = manager.feature_manager.create_feature("Loft", part, profile, None, name="Rendered Kernel Loft")
kernel = manager.parametric_manager.create_geometry_kernel("Rendered Kernel")
result = manager.parametric_manager.generate_feature_geometry(feature, workspace, kernel)
session = manager.geometry_sessions[-1]
topology = manager.parametric_manager.brep_topology_for(result.topology_id)

renderer = Renderer3D()
for item in (kernel, session, topology, result, feature, manager.bodies[0]):
    assert renderer._product_color(item, manager).isValid()

panel = PropertyPanel()
panel.set_workspace(workspace)
for item in (kernel, session, topology, result, manager.bodies[0], feature):
    panel.show_selection([item])
    assert panel.radius.text()
    assert panel.line_weight.text()

assert kernel in workspace.visible_product_objects()
assert session in workspace.visible_product_objects()
assert topology in workspace.visible_product_objects()
assert result in workspace.visible_product_objects()
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-geometry-kernel-renderer-property-ok")
