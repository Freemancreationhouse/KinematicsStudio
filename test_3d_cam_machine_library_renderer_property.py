import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import MachineCapabilities, MachineMetadata, ProductPart, RouterMachine, SpindleConfiguration, WorkEnvelope
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(7.0, 4.0, 1.0), name="Rendered Machine Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Machine Product")
part = manager.add_part(ProductPart("Rendered Machine Part", "Rendered Machine Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Machine CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Machine CAM Job", [part])
controller = manager.post_processor_manager.create_controller_profile("GRBL", "Rendered Machine GRBL", "1.1")
output = manager.post_processor_manager.create_output_configuration("Rendered Machine Output", "RENDERED")
post = manager.post_processor_manager.create_post_processor("Rendered Machine Post", controller, output, default=True)
library = manager.machine_library_manager.create_library("Rendered Machine Library")
machine = manager.machine_library_manager.create_machine(
    RouterMachine,
    library,
    "Rendered Router",
    "Router",
    MachineMetadata("Studio", "Router Pro", supported_controller="GRBL"),
    MachineCapabilities(work_envelope=WorkEnvelope(1000.0, 750.0, 100.0), spindle_configuration=SpindleConfiguration(maximum_rpm=18000.0)),
)
profile = manager.machine_library_manager.create_profile(machine, cam_job, post, controller, name="Rendered Machine Profile", validation_status="Ready")
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

panel.show_selection([library])
assert "Machines: 1" in panel.radius.text()

panel.show_selection([machine])
assert "Machine: Router" in panel.radius.text()
assert "Router Pro" in panel.width.text()
assert "RPM: 18000" in panel.line_weight.text()

panel.show_selection([profile])
assert "Profile:" in panel.radius.text()
assert "Validation: Ready" in panel.line_type.text()
assert "Machine assignment metadata only" in panel.line_weight.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-machine-library-renderer-property-ok")
