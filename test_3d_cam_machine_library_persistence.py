import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import MachineCapabilities, MachineMetadata, ProductPart, RouterMachine, TravelLimits, WorkEnvelope


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(8.0, 5.0, 1.5), name="Persisted Machine Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Machine Product")
part = manager.add_part(ProductPart("Persisted Machine Part", "Persisted Machine Mesh"))
cam_document = manager.cam_manager.create_document("Persisted Machine CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Machine CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Persisted Setup")
tool_library = manager.tool_library_manager.create_library("Persisted Machine Tools")
controller = manager.post_processor_manager.create_controller_profile("LinuxCNC", "Persisted LinuxCNC", "2.9")
output = manager.post_processor_manager.create_output_configuration("Persisted Machine Output", "PERSISTED")
post = manager.post_processor_manager.create_post_processor("Persisted Machine Post", controller, output, default=True)
library = manager.machine_library_manager.create_library("Persisted Machine Library")
machine = manager.machine_library_manager.create_machine(
    RouterMachine,
    library,
    "Persisted Router",
    "Router",
    MachineMetadata("Studio", "Router 900", firmware="2.0", supported_controller="LinuxCNC", favorite=True),
    MachineCapabilities(work_envelope=WorkEnvelope(900.0, 600.0, 120.0), travel_limits=TravelLimits(900.0, 600.0, 120.0)),
)
profile = manager.machine_library_manager.create_profile(
    machine,
    cam_job,
    post,
    controller,
    tool_library,
    setup,
    "Persisted Machine Profile",
    validation_status="Ready",
    warning_count=1,
)
workspace.selection.select(profile)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_machine_library.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_library = restored.machine_libraries[0]
    restored_machine = restored.machine_definitions[0]
    restored_profile = restored.machine_profiles[0]

    assert restored_library.name == "Persisted Machine Library"
    assert restored_library.machine_ids == [restored_machine.id]
    assert restored_machine.machine_type == "Router"
    assert restored_machine.metadata.manufacturer == "Studio"
    assert restored_machine.capabilities.work_envelope.width == 900.0
    assert restored_machine.capabilities.travel_limits.y == 600.0
    assert restored_profile.cam_job_id == restored.cam_jobs[0].id
    assert restored_profile.post_processor_id == restored.post_processors[0].id
    assert restored_profile.validation.warning_count == 1
    assert restored_profile.selected is True
    assert restored.machine_statistics.machines == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-machine-library-persistence-ok")
