from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductCurve, ProductPart, RouterBit
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(12.0, 8.0, 1.5), name="Router Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Router Product")
part = manager.add_part(ProductPart("Router Part", "Router Mesh"))
curve = manager.curve_manager.add_item(ProductCurve("Router Curve", part.id))
cam_document = manager.cam_manager.create_document("Router CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Router CAM Job", [part, curve])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Router Setup")

library = manager.tool_library_manager.create_library("Router Tools")
category = manager.tool_library_manager.create_category(library, "Router Bits")
router_bit = manager.tool_library_manager.create_tool(RouterBit, library, category, "Compression Bit")
feed_speed = manager.tool_library_manager.create_feed_speed_profile(router_bit, name="Plywood Feed")

dust = manager.router_manager.create_dust_collection_profile("Shop Vac")
profile = manager.router_manager.create_metadata_profile(
    "Plywood Router Profile",
    safe_height=20.0,
    clearance_height=10.0,
    retract_height=5.0,
    tabs_enabled=True,
    tab_width=8.0,
    tab_height=1.5,
    tab_count=4,
    bridges_enabled=True,
    bridge_width=10.0,
    bridge_height=1.0,
    bridge_count=2,
    onion_skin_enabled=True,
    onion_skin_thickness=0.4,
    dust_collection_profile=dust,
)
fixture = manager.router_manager.create_fixture("Vacuum Fixture", [part])
clamp = manager.router_manager.create_clamp_avoidance_region("Front Clamp", [curve])
router_job = manager.router_manager.create_router_job(cam_job, "Panel Router Job")

operation_types = [
    "Profile Cut",
    "Inside Profile",
    "Outside Profile",
    "Centerline",
    "Pocket Router",
    "V-Carve",
    "Engrave Router",
    "Chamfer Router",
    "Surfacing",
    "Adaptive Router",
]
operations = [
    manager.router_manager.create_operation(
        router_job,
        setup,
        operation_type,
        [part, curve],
        f"{operation_type} Definition",
        router_bit,
        feed_speed_profile=feed_speed,
        router_profile=profile,
        fixtures=[fixture],
        clamp_avoidance_regions=[clamp],
        cut_depth=6.0,
        step_down=2.0,
        step_over=1.5,
        pass_count=3,
        tabs_enabled=True,
        bridges_enabled=True,
        onion_skin_enabled=True,
        material_direction_placeholder="Grain",
        group="Router",
        order=index,
    )
    for index, operation_type in enumerate(operation_types)
]
manager.operation_manager.set_enabled(operations[-1], False)

stats = manager.router_manager.statistics()
ordered = manager.cam_operations_for_job(cam_job)

assert ordered[0].operation_type == "Profile Cut"
assert ordered[-1].operation_type == "Adaptive Router"
assert stats.router_jobs == 1
assert stats.router_operations == len(operations)
assert stats.fixtures == 1
assert stats.clamp_avoidance_regions == 1
assert stats.metadata_profiles == 1
assert stats.disabled == 1
assert operations[0].parameters.properties["cut_depth"] == 6.0
assert operations[0].parameters.properties["pass_count"] == 3
assert operations[0].router_profile.tabs.count == 4
assert operations[0].router_profile.bridges.count == 2
assert operations[0].router_profile.onion_skin.thickness == 0.4
assert operations[0].router_metadata.fixture_ids == [fixture.id]
assert operations[0].router_metadata.clamp_avoidance_ids == [clamp.id]
assert operations[0].segments() == []
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 50

print("3d-cam-router-manager-ok")
