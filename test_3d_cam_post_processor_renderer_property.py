import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(7.0, 4.0, 1.0), name="Rendered Post Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Post Product")
part = manager.add_part(ProductPart("Rendered Post Part", "Rendered Post Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Post CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Post CAM Job", [part])

controller = manager.post_processor_manager.create_controller_profile("GRBL", "Rendered GRBL", "1.1", units="mm")
output = manager.post_processor_manager.create_output_configuration("Rendered Output", "RENDERED", work_offset="G54", file_extension=".gcode")
template = manager.post_processor_manager.create_output_template("Rendered Template", "Header")
post = manager.post_processor_manager.create_post_processor("Rendered Post", controller, output, default=True)
profile = manager.post_processor_manager.create_profile(post, cam_job, controller, output, [template], "Rendered Profile", validation_status="Ready")
workspace.selection.select(profile)

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

panel.show_selection([post])
assert "Post Processor:" in panel.radius.text()
assert "No G-Code generation" in panel.line_weight.text()

panel.show_selection([profile])
assert "Profile:" in panel.radius.text()
assert "Validation: Ready" in panel.line_type.text()

panel.show_selection([controller])
assert "Controller: GRBL" in panel.radius.text()
assert "Units: mm" in panel.width.text()

panel.show_selection([output])
assert "Program: RENDERED" in panel.radius.text()
assert "Extension: .gcode" in panel.height.text()

panel.show_selection([template])
assert "Template: Header" in panel.radius.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-post-processor-renderer-property-ok")
