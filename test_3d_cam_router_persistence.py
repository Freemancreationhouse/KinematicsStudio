import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductCurve, ProductPart, RouterBit


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(10.0, 5.0, 1.0), name="Persisted Router Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted Router Product")
part = manager.add_part(ProductPart("Persisted Router Part", "Persisted Router Mesh"))
curve = manager.curve_manager.add_item(ProductCurve("Persisted Router Curve", part.id))
cam_document = manager.cam_manager.create_document("Persisted Router CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Persisted Router CAM Job", [part, curve])
setup = manager.manufacturing_setup_manager.create_setup(cam_job, [part], "Box", name="Persisted Router Setup")
library = manager.tool_library_manager.create_library("Persisted Router Tools")
category = manager.tool_library_manager.create_category(library, "Persisted Bits")
router_bit = manager.tool_library_manager.create_tool(RouterBit, library, category, "Persisted Router Bit")
feed_speed = manager.tool_library_manager.create_feed_speed_profile(router_bit, name="Persisted Router Feed")
dust = manager.router_manager.create_dust_collection_profile("Persisted Dust")
profile = manager.router_manager.create_metadata_profile(
    "Persisted Router Profile",
    safe_height=18.0,
    clearance_height=9.0,
    tab_count=3,
    tabs_enabled=True,
    onion_skin_enabled=True,
    onion_skin_thickness=0.3,
    dust_collection_profile=dust,
)
fixture = manager.router_manager.create_fixture("Persisted Fixture", [part])
clamp = manager.router_manager.create_clamp_avoidance_region("Persisted Clamp", [curve])
router_job = manager.router_manager.create_router_job(cam_job, "Persisted Router Job")
operation = manager.router_manager.create_operation(
    router_job,
    setup,
    "Profile Cut",
    [part, curve],
    "Persisted Profile Cut",
    router_bit,
    feed_speed_profile=feed_speed,
    router_profile=profile,
    fixtures=[fixture],
    clamp_avoidance_regions=[clamp],
    cut_depth=5.0,
    step_down=1.25,
    pass_count=4,
)
manager.operation_manager.set_enabled(operation, False)
workspace.selection.select(operation)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_router.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_operation = restored.cam_operations[0]

    assert restored_operation.name == "Persisted Profile Cut"
    assert restored_operation.operation_type == "Profile Cut"
    assert restored_operation.parameters.properties["cut_depth"] == 5.0
    assert restored_operation.parameters.properties["pass_count"] == 4
    assert restored_operation.router_profile.tabs.count == 3
    assert restored_operation.router_profile.onion_skin.thickness == 0.3
    assert restored_operation.router_metadata.fixture_ids == [restored.router_fixtures[0].id]
    assert restored_operation.router_metadata.clamp_avoidance_ids == [restored.clamp_avoidance_regions[0].id]
    assert restored_operation.metadata.enabled is False
    assert restored_operation.selected is True
    assert restored.router_statistics.router_operations == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-router-persistence-ok")
