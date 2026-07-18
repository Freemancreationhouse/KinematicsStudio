import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import MachineCapabilities, ProductPart, PrinterProfileMetadata, WorkEnvelope


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(9.0, 7.0, 3.0), name="Persisted Slicer Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Slicer Product")
part = manager.add_part(ProductPart("Persisted Slicer Part", "Persisted Slicer Mesh"))
cam_document = manager.cam_manager.create_document("Persisted Slicer CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Slicer CAM Job", [part])
machine_library = manager.machine_library_manager.create_library("Persisted Printer Library")
printer = manager.slicer_manager.create_printer_profile(
    "SLA",
    machine_library,
    "Persisted SLA",
    capabilities=MachineCapabilities(work_envelope=WorkEnvelope(145.0, 145.0, 180.0)),
    printer_metadata=PrinterProfileMetadata(0.0, 0.025, 0.1, resin_vat_placeholder=True),
)
controller = manager.post_processor_manager.create_controller_profile("Marlin", "Persisted Slicer Controller", "2.1", additive_mode_placeholder=True)
output = manager.post_processor_manager.create_output_configuration("Persisted Slicer Output", "PERSISTED_PRINT")
post = manager.post_processor_manager.create_post_processor("Persisted Slicer Post", controller, output)
machine_profile = manager.machine_library_manager.create_profile(printer, cam_job, post, controller, machine_library, name="Persisted Printer Assignment")
post_profile = manager.post_processor_manager.create_profile(post, cam_job, controller, output, name="Persisted Print Post")
slice_profile = manager.slicer_manager.create_profile(
    "Persisted Slice Profile",
    machine_profile,
    None,
    post_profile,
    technology="SLA",
    layer_height=0.05,
    layer_count=240,
    resin_volume=50.0,
    resin_weight=55.0,
    estimated_time_seconds=5400.0,
    estimated_weight=55.0,
)
slice_job = manager.slicer_manager.create_job(cam_job, slice_profile, "Persisted Slice Job")
operation = manager.slicer_manager.create_operation(slice_job, [part], slice_profile, "Persisted Slice Operation")
workspace.selection.select(slice_profile)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_slicer.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_printer = restored.machine_definitions[0]
    restored_profile = restored.slice_profiles[0]
    restored_job = restored.slice_jobs[0]
    restored_operation = restored.slice_operations[0]

    assert restored_printer.machine_type == "SLA"
    assert restored_printer.printer_metadata.resin_vat_placeholder is True
    assert restored_profile.print_profile.layer.layer_height == 0.05
    assert restored_profile.layer_definition.layer_count == 240
    assert restored_profile.layer_definition.resin_estimate.volume == 50.0
    assert restored_profile.layer_definition.weight_estimate.weight == 55.0
    assert restored_profile.selected is True
    assert restored_job.operation_ids == [restored_operation.id]
    assert restored.slice_statistics.jobs == 1
    assert restored.layer_statistics.layer_count == 240
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-slicer-persistence-ok")
