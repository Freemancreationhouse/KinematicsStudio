import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.product import CurveDefinition, ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(5.0, 5.0, 5.0), name="Rendered Curve Reference Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Curve Reference Product")
part = manager.add_part(ProductPart("Rendered Curve Reference Part", "Rendered Curve Reference Mesh"))
curve = manager.curve_manager.create_curve(
    "SplineCurve",
    part,
    CurveDefinition(part.id, mesh_entity_ids=["Rendered Curve Reference Mesh"], marker_points=[Vector3(0, 0, 0), Vector3(1, 1, 0)]),
)
reference = manager.reference_geometry_manager.create_axis(part, "Axis through Edge", [curve.id])
construction = manager.construction_geometry_manager.create("ConstructionPlane", part, [reference.id])
workspace.selection.select(curve)

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

panel.show_selection([curve])
assert panel.type.text() == "SplineCurve"
assert "Curve: SplineCurve" in panel.radius.text()
assert "References:" in panel.width.text()

panel.show_selection([reference])
assert panel.type.text() == "ReferenceAxis"
assert "Reference: ReferenceAxis" in panel.radius.text()
assert "Targets: 1" in panel.width.text()

panel.show_selection([construction])
assert panel.type.text() == "ConstructionPlane"
assert "Construction: ConstructionPlane" in panel.radius.text()
assert "References: 1" in panel.width.text()

panel.show_selection([part])
assert "Curves: 1" in panel.radius.text()
assert "Refs: 1" in panel.radius.text()
assert "Construction: 1" in panel.radius.text()

print("3d-product-curve-reference-renderer-property-ok")
