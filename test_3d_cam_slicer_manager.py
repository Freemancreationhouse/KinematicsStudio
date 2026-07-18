from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    FDMPrinterProfile,
    MachineCapabilities,
    MachineMetadata,
    MachineProfile,
    MaterialProfile,
    PostProcessorProfile,
    PrinterProfileMetadata,
    ProductPart,
    WorkEnvelope,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(12.0, 8.0, 4.0), name="Slicer Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Slicer Product")
part = manager.add_part(ProductPart("Slicer Part", "Slicer Mesh"))
cam_document = manager.cam_manager.create_document("Slicer CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Slicer CAM Job", [part])

machine_library = manager.machine_library_manager.create_library("Printer Library")
printer = manager.slicer_manager.create_printer_profile(
    "FDM",
    machine_library,
    "FDM Printer",
    MachineMetadata("Studio", "FDM 300", firmware="Marlin", supported_controller="Marlin"),
    MachineCapabilities(work_envelope=WorkEnvelope(300.0, 300.0, 250.0)),
    PrinterProfileMetadata(0.4, 0.08, 0.28, 260.0, 110.0, "Marlin", 2, True),
)
controller = manager.post_processor_manager.create_controller_profile("Marlin", "Slicer Marlin", "2.1", additive_mode_placeholder=True)
output = manager.post_processor_manager.create_output_configuration("Slicer Output", "PRINT", file_extension=".gcode")
post = manager.post_processor_manager.create_post_processor("Slicer Post", controller, output, default=True)
machine_profile = manager.machine_library_manager.create_profile(printer, cam_job, post, controller, machine_library, name="Printer Assignment")
post_profile = manager.post_processor_manager.create_profile(post, cam_job, controller, output, name="Print Post Profile")
material = manager.laser_plasma_manager.create_material_profile("PLA", "PLA", thickness=1.75)

slice_profile = manager.slicer_manager.create_profile(
    "Draft PLA",
    machine_profile,
    material,
    post_profile,
    layer_height=0.2,
    first_layer_height=0.24,
    infill_percentage=15.0,
    support_enabled=True,
    support_density=12.0,
    brim=True,
    cooling_enabled=True,
    fan_speed=80.0,
    retraction_distance=1.2,
    print_speed=70.0,
    travel_speed=140.0,
    layer_count=100,
    estimated_time_seconds=3600.0,
    filament_length=1200.0,
    filament_weight=42.0,
    estimated_weight=42.0,
    technology="FDM",
    status="Ready",
)
slice_job = manager.slicer_manager.create_job(cam_job, slice_profile, "Draft Print Job")
operation = manager.slicer_manager.create_operation(slice_job, [part], slice_profile, "Draft Slice Operation")
stats = manager.slicer_manager.statistics()

assert isinstance(printer, FDMPrinterProfile)
assert printer in manager.machine_definitions
assert printer.id in machine_library.machine_ids
assert isinstance(machine_profile, MachineProfile)
assert isinstance(post_profile, PostProcessorProfile)
assert stats.jobs == 1
assert stats.operations == 1
assert stats.profiles == 1
assert stats.enabled_jobs == 1
assert stats.printer_profiles == 1
assert stats.layer_definitions == 1
assert stats.estimated_time_seconds == 3600.0
assert manager.layer_statistics.layer_count == 100
assert manager.layer_statistics.estimated_weight == 42.0
assert slice_profile.machine_profile_id == machine_profile.id
assert slice_profile.post_processor_profile_id == post_profile.id
assert slice_profile.print_profile.material_reference.material_profile_id == material.id
assert slice_profile.print_profile.cooling.properties["fan_speed"] == 80.0
assert slice_job.operation_ids == [operation.id]
assert operation.target_ids == [part.id]
assert operation.segments() == []
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 12

print("3d-cam-slicer-manager-ok")
