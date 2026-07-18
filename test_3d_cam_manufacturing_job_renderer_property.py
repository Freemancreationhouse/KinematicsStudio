import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ManufacturingMetrics, ProductPart, ValidationWarning
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(6.0, 4.0, 2.0), name="Rendered Manufacturing Job Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Manufacturing Job Product")
part = manager.add_part(ProductPart("Rendered Manufacturing Job Part", "Rendered Manufacturing Job Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Manufacturing Job CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Manufacturing Job CAM Job", [part])
job = manager.manufacturing_job_manager.create_job("Rendered Manufacturing Job", cam_job=cam_job, priority="High", status="Ready")
validation_profile = manager.manufacturing_validation_manager.create_profile("Rendered Validation Profile", [cam_job])
validation_result = manager.manufacturing_validation_manager.create_result(validation_profile, job, "Ready", [ValidationWarning("Rendered warning", [job.id])])
sheet = manager.manufacturing_job_manager.create_setup_sheet(job, name="Rendered Setup Sheet", operator_notes="Check stock")
dashboard = manager.manufacturing_job_manager.create_dashboard("Rendered Dashboard", [job], ManufacturingMetrics(ready_jobs=1, pending_jobs=0, warning_jobs=0))
queue = manager.manufacturing_job_manager.create_queue("Rendered Queue")
workspace.selection.select(job)

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

panel.show_selection([job])
assert "Manufacturing Job:" in panel.radius.text()
assert "Ready" in panel.line_type.text()
assert "Priority: High" in panel.line_weight.text()

panel.show_selection([validation_profile])
assert "Validation Profile:" in panel.radius.text()
assert "no validation algorithms" in panel.line_weight.text()

panel.show_selection([validation_result])
assert "Validation Result:" in panel.radius.text()
assert "Issues: 1" in panel.line_type.text()

panel.show_selection([sheet])
assert "Setup Sheet:" in panel.radius.text()
assert "Shop-floor document metadata" in panel.line_weight.text()

panel.show_selection([dashboard])
assert "Dashboard Jobs: 1" in panel.radius.text()
assert "Manufacturing Dashboard" in panel.line_type.text()

panel.show_selection([queue])
assert "Queue metadata" in panel.line_type.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-manufacturing-job-renderer-property-ok")
