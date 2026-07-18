from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, RouterBit
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(10.0, 6.0, 2.0), name="Post Processor Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Post Processor Product")
part = manager.add_part(ProductPart("Post Processor Part", "Post Processor Mesh"))
cam_document = manager.cam_manager.create_document("Post Processor CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Post Processor CAM Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Post Processor Setup")

library = manager.tool_library_manager.create_library("Post Tools")
category = manager.tool_library_manager.create_category(library, "Router Bits")
tool = manager.tool_library_manager.create_tool(RouterBit, library, category, "Post Router Bit")
feed = manager.tool_library_manager.create_feed_speed_profile(tool, name="Post Feed")
router_job = manager.router_manager.create_router_job(cam_job, "Post Router Job")
operation = manager.router_manager.create_operation(
    router_job,
    setup,
    "Profile Cut",
    [part],
    "Post Profile Cut",
    tool,
    feed_speed_profile=feed,
    cut_depth=4.0,
)

controller_types = [
    "GRBL",
    "Marlin",
    "Klipper",
    "LinuxCNC",
    "Fanuc",
    "Haas",
    "Mach3",
    "Mach4",
    "Smoothieware",
    "Duet",
    "Masso",
    "GenericGCode",
]
controllers = [
    manager.post_processor_manager.create_controller_profile(
        controller,
        f"{controller} Profile",
        "1.0",
        supported_g_codes=["G0", "G1", "G2", "G3"],
        supported_m_codes=["M3", "M5"],
        units="mm",
        coordinate_mode="Absolute",
        laser_mode_placeholder=controller in {"GRBL", "Marlin"},
    )
    for controller in controller_types
]
output = manager.post_processor_manager.create_output_configuration(
    "Router Output",
    "PANEL_A",
    units="mm",
    coordinate_mode="Absolute",
    work_offset="G54",
    safe_start_block="G90 G21",
    safe_end_block="M30",
    tool_change_policy="Manual",
    spindle_start="M3",
    spindle_stop="M5",
    comment_style="Parentheses",
    line_numbering_placeholder=True,
    file_extension=".nc",
)
template = manager.post_processor_manager.create_output_template("Router Header Template", "Header", "(header)")
post = manager.post_processor_manager.create_post_processor(
    "Generic Router Post",
    controllers[0],
    output,
    default=True,
)
profile = manager.post_processor_manager.create_profile(
    post,
    cam_job,
    controllers[0],
    output,
    [template],
    "Router Job Post Profile",
    operations=[operation],
    supports_arcs=True,
    supports_tool_changes=True,
    validation_status="Ready",
)

stats = manager.post_processor_manager.statistics()

assert stats.post_processors == 1
assert stats.profiles == 1
assert stats.controller_profiles == len(controller_types)
assert stats.output_configurations == 1
assert stats.output_templates == 1
assert stats.enabled_profiles == 1
assert stats.default_processors == 1
assert manager.output_statistics.configurations == 1
assert post.default is True
assert post.profile_ids == [profile.id]
assert profile.cam_job_id == cam_job.id
assert profile.machine_reference.operation_ids == [operation.id]
assert output.coordinates.work_offset == "G54"
assert output.metadata.file_extension == ".nc"
assert controllers[0].metadata.supported_g_codes == ["G0", "G1", "G2", "G3"]
assert template.segments() == []
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 18

print("3d-cam-post-processor-manager-ok")
