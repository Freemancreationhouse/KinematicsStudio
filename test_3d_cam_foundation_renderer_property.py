import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EngineeringMaterial, ProductPart, SolidBody
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(4.0, 3.0, 2.0), name="Rendered CAM Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered CAM Product")
part = manager.add_part(ProductPart("Rendered CAM Part", "Rendered CAM Mesh"))
body = manager.add_body_item(SolidBody("Rendered CAM Body", part.id, mesh.name))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Rendered Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Rendered CAM Document")
job = manager.cam_manager.create_job(cam_document, "Rendered CAM Job", [part, body])
setup = manager.manufacturing_setup_manager.create_setup(job, [part, body], "Box", material, "Rendered Setup")
operation = manager.operation_manager.create_operation(job, setup, "Facing", [part], "Rendered Facing")
workspace.selection.select(operation)

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

panel.show_selection([cam_document])
assert panel.type.text() == "CAMDocument"
assert "CAM Jobs: 1" in panel.radius.text()

panel.show_selection([job])
assert panel.type.text() == "CAMJob"
assert "Setups: 1" in panel.radius.text()
assert "Operations: 1" in panel.radius.text()
assert "Active" in panel.line_type.text()

panel.show_selection([setup])
assert panel.type.text() == "ManufacturingSetup"
assert "Stock: Box" in panel.radius.text()
assert "Targets: 2" in panel.width.text()

panel.show_selection([operation])
assert panel.type.text() == "OperationDefinition"
assert "Operation: Facing" in panel.radius.text()
assert "Definition Only" in panel.line_weight.text()

panel.show_selection([part])
assert "CAM Jobs: 1" in panel.radius.text()
assert "CAM Setups: 1" in panel.radius.text()
assert "CAM Ops: 1" in panel.radius.text()

assert len(workspace.scene3d.entities()) == 1

print("3d-cam-foundation-renderer-property-ok")
