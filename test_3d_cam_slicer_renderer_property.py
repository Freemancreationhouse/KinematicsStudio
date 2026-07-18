import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import MachineCapabilities, PrinterProfileMetadata, ProductPart, WorkEnvelope
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
mesh = MeshEntity(MeshData.box(6.0, 4.0, 2.0), name="Rendered Slicer Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Rendered Slicer Product")
part = manager.add_part(ProductPart("Rendered Slicer Part", "Rendered Slicer Mesh"))
cam_document = manager.cam_manager.create_document("Rendered Slicer CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Rendered Slicer CAM Job", [part])
machine_library = manager.machine_library_manager.create_library("Rendered Printer Library")
printer = manager.slicer_manager.create_printer_profile(
    "FDM",
    machine_library,
    "Rendered FDM",
    capabilities=MachineCapabilities(work_envelope=WorkEnvelope(220.0, 220.0, 250.0)),
    printer_metadata=PrinterProfileMetadata(0.4, 0.08, 0.28),
)
machine_profile = manager.machine_library_manager.create_profile(printer, cam_job, name="Rendered Printer Assignment")
slice_profile = manager.slicer_manager.create_profile("Rendered Slice Profile", machine_profile, layer_height=0.2, infill_percentage=25.0, layer_count=80, status="Ready")
slice_job = manager.slicer_manager.create_job(cam_job, slice_profile, "Rendered Slice Job")
operation = manager.slicer_manager.create_operation(slice_job, [part], slice_profile, "Rendered Slice Operation")
workspace.selection.select(slice_job)

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

panel.show_selection([printer])
assert "Machine: FDM" in panel.radius.text()
assert "Printer: nozzle 0.4" in panel.line_type.text()

panel.show_selection([slice_profile])
assert "Slice Profile:" in panel.radius.text()
assert "Layer: 0.2" in panel.width.text()
assert "Layer metadata only" in panel.line_weight.text()

panel.show_selection([slice_job])
assert "Slice Job: 1 operations" in panel.radius.text()
assert "No slicing or G-Code generation" in panel.line_weight.text()

panel.show_selection([operation])
assert "Slice Operation:" in panel.radius.text()
assert "No extrusion paths" in panel.line_weight.text()
assert len(workspace.scene3d.entities()) == 1

print("3d-cam-slicer-renderer-property-ok")
