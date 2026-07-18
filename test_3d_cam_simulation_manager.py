from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, RouterBit, WarningMetadata
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(12.0, 8.0, 4.0), name="Simulation Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Simulation Product")
part = manager.add_part(ProductPart("Simulation Part", "Simulation Mesh"))
cam_document = manager.cam_manager.create_document("Simulation CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Simulation CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Simulation Setup")
tool_library = manager.tool_library_manager.create_library("Simulation Tools")
category = manager.tool_library_manager.create_category(tool_library, "Router Bits")
tool = manager.tool_library_manager.create_tool(RouterBit, tool_library, category, "Simulation Router Bit")
machine_library = manager.machine_library_manager.create_library("Simulation Machines")
machine = manager.slicer_manager.create_printer_profile("FDM", machine_library, "Simulation Printer")
machine_profile = manager.machine_library_manager.create_profile(machine, cam_job, tool_library=tool_library, setup=setup, name="Simulation Machine Profile")
slice_profile = manager.slicer_manager.create_profile("Simulation Slice Profile", machine_profile, layer_count=88, estimated_weight=35.0)
slice_job = manager.slicer_manager.create_job(cam_job, slice_profile, "Simulation Slice Job")
warning = WarningMetadata("Warning", "Clearance metadata pending", [part.id])

profile = manager.simulation_manager.create_profile(
    "Print",
    "Print Simulation Profile",
    machine_profile=machine_profile,
    tool=tool,
    tool_library=tool_library,
    setup=setup,
    slice_job=slice_job,
    warnings=[warning],
    ready=True,
    simulation_status="Ready",
    estimated_runtime=4200.0,
    estimated_travel_distance=1200.0,
    estimated_material_usage=35.0,
    estimated_layer_count=88,
    estimated_machine_motion=150,
    estimated_tool_changes=1,
    estimated_setup_time=12.0,
    estimated_cooldown_placeholder=5.0,
    estimated_energy_placeholder=2.5,
)
job = manager.simulation_manager.create_job(cam_job, slice_job, profile, "Simulation Job", enabled=True, result_status="Ready")
stats = manager.simulation_manager.statistics()

assert stats.jobs == 1
assert stats.profiles == 1
assert stats.enabled_jobs == 1
assert stats.warnings == 1
assert stats.ready_profiles == 1
assert stats.cam_references == 1
assert stats.slice_references == 1
assert profile.metadata.simulation_type == "Print"
assert profile.estimate.estimated_runtime == 4200.0
assert profile.estimate.layer_count == 88
assert profile.validation.machine_reference.machine_profile_id == machine_profile.id
assert profile.validation.tool_reference.tool_id == tool.id
assert profile.validation.fixture_reference.setup_id == setup.id
assert profile.validation.readiness.ready is True
assert job.cam_job_id == cam_job.id
assert job.slice_job_id == slice_job.id
assert job.profile_id == profile.id
assert profile.segments() == []
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 12

print("3d-cam-simulation-manager-ok")
