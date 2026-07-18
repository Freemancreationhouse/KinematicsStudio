import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.coordination_package import PackageMetadata
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
entity = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Rendered Package Box")
entity.id = "rendered-package-box"
workspace.add_3d_entity(entity)
workspace.reference_manager.create_model("Rendered Reference", "rendered.obj")
package = workspace.coordination_package_manager.create_delivery_package(
    "Rendered Package",
    workspace,
    PackageMetadata("Author", "Recipient", "Rendered package marker", "1.1", "Ready"),
)
workspace.selection.select(package)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.show_selection([package])

assert "CoordinationPackage" in panel.type.text()
assert panel.content.text() == "Rendered package marker"
assert "Status: Ready" in panel.alignment.text()
assert "Version: 1.1" in panel.dimension_style.text()
assert "Refs: 1" in panel.line_type.text()
assert "Validation: Valid" in panel.diameter.text()

print("3d-coordination-package-renderer-property-ok")
