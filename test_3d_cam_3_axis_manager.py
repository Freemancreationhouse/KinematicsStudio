from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EndMill, EngineeringMaterial, ProductPart, ProductCurve, SurfaceBody
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(8.0, 5.0, 2.0), name="3 Axis Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("3 Axis Product")
part = manager.add_part(ProductPart("3 Axis Part", "3 Axis Mesh"))
surface_body = manager.surface_manager.add_item(SurfaceBody("3 Axis Surface", part.id, mesh.name))
curve = manager.curve_manager.add_item(ProductCurve("3 Axis Boundary Curve", part.id))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("3 Axis Aluminium", "Aluminium"))

cam_document = manager.cam_manager.create_document("3 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "3 Axis Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "3 Axis Setup")

library = manager.tool_library_manager.create_library("3 Axis Tools")
category = manager.tool_library_manager.create_category(library, "Finishing")
tool = manager.tool_library_manager.create_tool(EndMill, library, category, "6mm Ball End Mill", diameter=6.0)
profile = manager.tool_library_manager.create_feed_speed_profile(tool, material, "3 Axis Feeds")

surface_selection = manager.three_axis_operation_manager.create_surface_selection(
    part,
    [surface_body],
    mesh_entities=[mesh],
    face_ids=["face-a", "face-b"],
)
region = manager.three_axis_operation_manager.create_machining_region(part, [surface_body], face_ids=["face-a"])
containment = manager.three_axis_operation_manager.create_boundary(part, "Containment", [curve], name="3 Axis Containment")
avoid = manager.three_axis_operation_manager.create_boundary(part, "Avoid", [curve], name="3 Axis Avoid")

operation_types = [
    "Parallel",
    "Waterline",
    "Scallop",
    "Pencil",
    "Horizontal",
    "Vertical",
    "Rest Machining 3 Axis",
    "Morph",
    "Flow",
    "Projection",
]
operations = [
    manager.three_axis_operation_manager.create_operation(
        job,
        setup,
        operation_type,
        [part, surface_body],
        f"{operation_type} Definition",
        tool,
        profile,
        surface_selection,
        region,
        [containment, avoid],
        tolerance=0.02,
        stepover=0.35,
        stepdown=0.8,
        maximum_cusp_height=0.01,
        boundary_mode="Inside",
        cut_direction="Zig Zag",
        group="3 Axis",
        order=index,
    )
    for index, operation_type in enumerate(operation_types)
]
manager.operation_manager.set_enabled(operations[-1], False)

op_stats = manager.operation_manager.statistics()
boundary_stats = manager.three_axis_operation_manager.statistics()
ordered = manager.cam_operations_for_job(job)

assert ordered[0].operation_type == "Parallel"
assert ordered[-1].operation_type == "Projection"
assert op_stats.operations == len(operations)
assert manager.three_axis_statistics.operations == len(operations)
assert manager.three_axis_statistics.disabled == 1
assert boundary_stats.surface_selections == 1
assert boundary_stats.machining_regions == 1
assert boundary_stats.containment == 1
assert boundary_stats.avoid == 1
assert operations[0].strategy.tolerance == 0.02
assert operations[0].strategy.stepover == 0.35
assert operations[0].three_axis_metadata.surface_selection_id == surface_selection.id
assert operations[0].three_axis_metadata.machining_region_id == region.id
assert operations[0].three_axis_metadata.boundary_ids == [containment.id, avoid.id]
assert all(operation.segments() == [] for operation in operations)
assert len(workspace.scene3d.entities()) == 1
assert len(manager.dependency_edges) >= 50

print("3d-cam-3-axis-manager-ok")
