import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, SurfaceFeatureOptions, SurfaceFeatureDefinition
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(5.0, 1.0, 5.0), name="Rendered Surface Mesh")
workspace.add_3d_entity(mesh)
manager = workspace.product_manager
manager.create_document("Rendered Surface Product")
part = manager.add_part(ProductPart("Rendered Surface Part", "Rendered Surface Mesh"))
surface_body = manager.surface_manager.create_surface_body(part, "Rendered Surface Mesh", "Rendered Surface Body")
surface_body.metadata.group = "A Surfaces"
loft = manager.feature_manager.create_feature("Loft Surface", part, body=surface_body)
loft.surface_definition = SurfaceFeatureDefinition(
    "Loft Surface",
    target_surface_ids=[surface_body.id],
    options=SurfaceFeatureOptions(profile_ids=["a", "b"], boundary_curve_ids=["edge-a"], offset_distance=2.0),
)
manager.feature_manager.apply_feature(loft, workspace)
trim = manager.surface_operation_manager.create_operation("Trim", part, surface_body)
workspace.selection.select(loft)

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

panel.show_selection([surface_body])
assert panel.type.text() == "SurfaceBody"
assert "Surface Features" in panel.radius.text()
assert "Group: A Surfaces" in panel.width.text()

panel.show_selection([loft])
assert panel.type.text() == "LoftSurfaceFeature"
assert "Surface: Loft Surface" in panel.radius.text()
assert "Profiles: 2" in panel.width.text()
assert "Offset: 2" in panel.diameter.text()

panel.show_selection([trim])
assert panel.type.text() == "TrimSurfaceFeature"
assert "Surface: Trim Surface" in panel.radius.text()

print("3d-product-surface-foundation-renderer-property-ok")
