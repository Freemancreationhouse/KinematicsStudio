from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    CNCMachine,
    GenericMachine,
    LaserMachine,
    MachineCapabilities,
    MachineMetadata,
    PlasmaMachine,
    PrinterMachine,
    ProductPart,
    RouterBit,
    RouterMachine,
    SpindleConfiguration,
    ToolChangerConfiguration,
    TravelLimits,
    WorkEnvelope,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(10.0, 6.0, 2.0), name="Machine Library Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Machine Library Product")
part = manager.add_part(ProductPart("Machine Library Part", "Machine Library Mesh"))
cam_document = manager.cam_manager.create_document("Machine Library CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Machine Library CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Machine Library Setup")

tool_library = manager.tool_library_manager.create_library("Machine Tools")
tool_category = manager.tool_library_manager.create_category(tool_library, "Router Bits")
tool = manager.tool_library_manager.create_tool(RouterBit, tool_library, tool_category, "Machine Router Bit")
feed = manager.tool_library_manager.create_feed_speed_profile(tool, name="Machine Feed")
router_job = manager.router_manager.create_router_job(cam_job, "Machine Router Job")
operation = manager.router_manager.create_operation(
    router_job,
    setup,
    "Profile Cut",
    [part],
    "Machine Profile Cut",
    tool,
    feed_speed_profile=feed,
    cut_depth=3.0,
)

controller = manager.post_processor_manager.create_controller_profile("GRBL", "Machine GRBL", "1.1")
output = manager.post_processor_manager.create_output_configuration("Machine Output", "MACHINE", file_extension=".gcode")
post = manager.post_processor_manager.create_post_processor("Machine Post", controller, output, default=True)

library = manager.machine_library_manager.create_library("Shop Machines")
capabilities = MachineCapabilities(
    work_envelope=WorkEnvelope(1200.0, 800.0, 150.0),
    travel_limits=TravelLimits(1200.0, 800.0, 150.0, 6000.0, 12000.0),
    spindle_configuration=SpindleConfiguration(maximum_rpm=24000.0, maximum_feed_rate=6000.0, rapid_rate=12000.0),
    tool_changer_configuration=ToolChangerConfiguration(True, 12, "ATC"),
)
machines = [
    manager.machine_library_manager.create_machine(CNCMachine, library, "CNC Mill", "CNC", MachineMetadata("Studio", "Mill 500", firmware="1.0", supported_controller="GRBL", supported_operations=["Facing", "Pocket"], favorite=True), capabilities),
    manager.machine_library_manager.create_machine(RouterMachine, library, "Router", "Router"),
    manager.machine_library_manager.create_machine(LaserMachine, library, "Laser", "Laser"),
    manager.machine_library_manager.create_machine(PlasmaMachine, library, "Plasma", "Plasma"),
    manager.machine_library_manager.create_machine(PrinterMachine, library, "Printer", "Printer"),
    manager.machine_library_manager.create_machine(GenericMachine, library, "Generic Machine", "Generic"),
]
profile = manager.machine_library_manager.create_profile(
    machines[0],
    cam_job,
    post,
    controller,
    tool_library,
    setup,
    "Primary CNC Assignment",
    operations=[operation],
    validation_status="Ready",
)
stats = manager.machine_library_manager.statistics()

assert stats.libraries == 1
assert stats.machines == 6
assert stats.profiles == 1
assert stats.categories == 6
assert stats.favorites == 1
assert stats.assignments == 1
assert manager.capability_statistics.tool_changers == 1
assert library.machine_ids == [machine.id for machine in machines]
assert library.profile_ids == [profile.id]
assert library.favorite_machine_ids == [machines[0].id]
assert profile.cam_job_id == cam_job.id
assert profile.post_processor_id == post.id
assert profile.controller_profile_id == controller.id
assert profile.tool_library_id == tool_library.id
assert profile.setup_id == setup.id
assert profile.profile_reference.operation_ids == [operation.id]
assert manager.machine_library_manager.search_machines("studio") == [machines[0]]
assert profile.segments() == []
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 14

print("3d-cam-machine-library-manager-ok")
