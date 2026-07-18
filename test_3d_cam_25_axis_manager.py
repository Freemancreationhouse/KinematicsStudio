from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    Drill,
    EndMill,
    EngineeringMaterial,
    ProductPart,
    ToolMetadata,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(6.0, 4.0, 1.0), name="25 Axis Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("25 Axis Product")
part = manager.add_part(ProductPart("25 Axis Part", "25 Axis Mesh"))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("25 Axis Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("25 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "25 Axis Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "25 Axis Setup")

library = manager.tool_library_manager.create_library("25 Axis Tools")
category = manager.tool_library_manager.create_category(library, "Milling")
end_mill = manager.tool_library_manager.create_tool(
    EndMill,
    library,
    category,
    "10mm End Mill",
    diameter=10.0,
    flute_length=25.0,
    overall_length=75.0,
    flutes=4,
    metadata=ToolMetadata(material="Carbide"),
)
drill = manager.tool_library_manager.create_tool(
    Drill,
    library,
    category,
    "6mm Drill",
    diameter=6.0,
    flute_length=30.0,
    overall_length=80.0,
    flutes=2,
)
profile = manager.tool_library_manager.create_feed_speed_profile(end_mill, material, "Aluminium Milling")

milling_types = ["Facing", "Pocket", "Contour", "Slot", "Adaptive Clearing", "Rest Machining"]
milling_operations = [
    manager.operation_manager.create_milling_operation(
        job,
        setup,
        operation_type,
        [part],
        f"{operation_type} Definition",
        end_mill,
        profile,
        depth=5.0,
        step_down=1.0,
        step_over=0.4,
        finish_pass=True,
        rough_pass=True,
        allowance=0.2,
        group="Milling",
        order=index,
    )
    for index, operation_type in enumerate(milling_types)
]

hole_types = ["Drill", "Peck Drill", "Bore", "CounterBore", "CounterSink", "Tap", "Thread Mill"]
hole_operations = [
    manager.operation_manager.create_hole_operation(
        job,
        setup,
        operation_type,
        [part],
        f"{operation_type} Definition",
        drill,
        profile,
        hole_depth=12.0,
        retract_height=3.0,
        peck_depth=2.0,
        cycle_type=operation_type,
        group="Holes",
        order=len(milling_types) + index,
    )
    for index, operation_type in enumerate(hole_types)
]
manager.operation_manager.set_enabled(milling_operations[1], False)
manager.operation_manager.rename_operation(milling_operations[0], "Facing Renamed")

stats = manager.operation_manager.statistics()
ordered = manager.cam_operations_for_job(job)

assert ordered[0].name == "Facing Renamed"
assert ordered[-1].operation_type == "Thread Mill"
assert stats.operations == len(milling_operations) + len(hole_operations)
assert stats.milling == len(milling_operations)
assert stats.hole_operations == len(hole_operations)
assert stats.disabled == 1
assert all(operation.segments() == [] for operation in milling_operations + hole_operations)
assert milling_operations[0].parameters.depth == 5.0
assert milling_operations[0].parameters.step_down == 1.0
assert milling_operations[0].parameters.finish_pass is True
assert milling_operations[0].parameters.tool_id == end_mill.id
assert milling_operations[0].parameters.feed_speed_profile_id == profile.id
assert hole_operations[0].parameters.hole_depth == 12.0
assert hole_operations[0].parameters.retract_height == 3.0
assert hole_operations[0].parameters.coolant_placeholder is True
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 40

print("3d-cam-25-axis-manager-ok")
