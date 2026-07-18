import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, WarningMetadata
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(6.0, 4.0, 2.0), name="Rendered Simulation Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Simulation Product")
part = manager.add_part(ProductPart("Rendered Simulation Part", "Rendered Simulation Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Simulation CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Simulation CAM Job", [part])
warning = WarningMetadata("Warning", "Fixture metadata pending", [part.id])
profile = manager.simulation_manager.create_profile("CNC", "Rendered CNC Simulation", warnings=[warning], ready=True, estimated_runtime=900.0, estimated_travel_distance=500.0)
job = manager.simulation_manager.create_job(cam_job, None, profile, "Rendered Simulation Job", result_status="Ready")
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

panel.show_selection([profile])
assert "Simulation: CNC" in panel.radius.text()
assert "Warnings: 1" in panel.line_type.text()
assert "Validation hooks only" in panel.line_weight.text()

panel.show_selection([job])
assert "Simulation Job:" in panel.radius.text()
assert "Ready" in panel.line_type.text()
assert "no simulation playback" in panel.line_weight.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-simulation-renderer-property-ok")
