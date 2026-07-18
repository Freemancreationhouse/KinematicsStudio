import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Drill, EndMill, EngineeringMaterial, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(5.0, 5.0, 1.0), name="Persisted 25 Axis Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted 25 Axis Product")
part = manager.add_part(ProductPart("Persisted 25 Axis Part", "Persisted 25 Axis Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Persisted Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Persisted 25 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "Persisted 25 Axis Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "Persisted 25 Axis Setup")
library = manager.tool_library_manager.create_library("Persisted 25 Axis Tools")
category = manager.tool_library_manager.create_category(library, "Persisted 25 Axis Category")
end_mill = manager.tool_library_manager.create_tool(EndMill, library, category, "Persisted End Mill", diameter=8.0)
drill = manager.tool_library_manager.create_tool(Drill, library, category, "Persisted Drill", diameter=4.0)
profile = manager.tool_library_manager.create_feed_speed_profile(end_mill, material, "Persisted Feeds")
facing = manager.operation_manager.create_milling_operation(
    job,
    setup,
    "Facing",
    [part],
    "Persisted Facing",
    end_mill,
    profile,
    depth=3.5,
    step_down=0.7,
    allowance=0.1,
    group="Milling",
)
drilling = manager.operation_manager.create_hole_operation(
    job,
    setup,
    "Peck Drill",
    [part],
    "Persisted Peck Drill",
    drill,
    profile,
    hole_depth=10.0,
    retract_height=2.5,
    peck_depth=1.0,
    group="Holes",
)
manager.operation_manager.set_enabled(drilling, False)
workspace.selection.select(facing)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_25_axis.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    restored_facing = restored.cam_operations[0]
    restored_drilling = restored.cam_operations[1]
    assert restored_facing.name == "Persisted Facing"
    assert restored_facing.operation_type == "Facing"
    assert restored_facing.parameters.depth == 3.5
    assert restored_facing.parameters.step_down == 0.7
    assert restored_facing.parameters.feed_speed_profile_id == restored.feed_speed_profiles[0].id
    assert restored_facing.selected is True
    assert restored_drilling.operation_type == "Peck Drill"
    assert restored_drilling.parameters.hole_depth == 10.0
    assert restored_drilling.parameters.peck_depth == 1.0
    assert restored_drilling.metadata.enabled is False
    assert restored.operation_statistics.milling == 1
    assert restored.operation_statistics.hole_operations == 1
    assert restored.operation_statistics.disabled == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-25-axis-persistence-ok")
