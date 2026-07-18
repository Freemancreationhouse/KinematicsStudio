import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import EndMill, EngineeringMaterial, ProductCurve, ProductPart, SurfaceBody


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(7.0, 4.0, 1.5), name="Persisted 3 Axis Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
manager.create_document("Persisted 3 Axis Product")
part = manager.add_part(ProductPart("Persisted 3 Axis Part", "Persisted 3 Axis Mesh"))
surface_body = manager.surface_manager.add_item(SurfaceBody("Persisted 3 Axis Surface", part.id, mesh.name))
curve = manager.curve_manager.add_item(ProductCurve("Persisted 3 Axis Boundary Curve", part.id))
material = manager.engineering_material_manager.add_item(EngineeringMaterial("Persisted 3 Axis Aluminium", "Aluminium"))
cam_document = manager.cam_manager.create_document("Persisted 3 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "Persisted 3 Axis Job", [part])
setup = manager.manufacturing_setup_manager.create_setup(job, [part], "Box", material, "Persisted 3 Axis Setup")
library = manager.tool_library_manager.create_library("Persisted 3 Axis Tools")
category = manager.tool_library_manager.create_category(library, "Persisted 3 Axis Category")
tool = manager.tool_library_manager.create_tool(EndMill, library, category, "Persisted 3 Axis End Mill", diameter=5.0)
profile = manager.tool_library_manager.create_feed_speed_profile(tool, material, "Persisted 3 Axis Feeds")
selection = manager.three_axis_operation_manager.create_surface_selection(part, [surface_body], mesh_entities=[mesh], face_ids=["f1"])
region = manager.three_axis_operation_manager.create_machining_region(part, [surface_body], face_ids=["f1"])
boundary = manager.three_axis_operation_manager.create_boundary(part, "Containment", [curve], name="Persisted 3 Axis Boundary")
operation = manager.three_axis_operation_manager.create_operation(
    job,
    setup,
    "Waterline",
    [part],
    "Persisted Waterline",
    tool,
    profile,
    selection,
    region,
    [boundary],
    tolerance=0.015,
    stepover=0.2,
    stepdown=0.6,
    maximum_cusp_height=0.005,
    boundary_mode="Inside",
    cut_direction="Climb",
    group="3 Axis",
)
manager.operation_manager.set_enabled(operation, False)
workspace.selection.select(operation)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "cam_3_axis.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_operation = restored.cam_operations[0]

    assert restored_operation.name == "Persisted Waterline"
    assert restored_operation.operation_type == "Waterline"
    assert restored_operation.strategy.tolerance == 0.015
    assert restored_operation.strategy.stepover == 0.2
    assert restored_operation.strategy.stepdown == 0.6
    assert restored_operation.strategy.maximum_cusp_height == 0.005
    assert restored_operation.three_axis_metadata.surface_selection_id == restored.three_axis_surface_selections[0].id
    assert restored_operation.three_axis_metadata.machining_region_id == restored.three_axis_machining_regions[0].id
    assert restored_operation.three_axis_metadata.boundary_ids == [restored.three_axis_boundaries[0].id]
    assert restored_operation.metadata.enabled is False
    assert restored_operation.selected is True
    assert restored.boundary_statistics.containment == 1
    assert restored.three_axis_statistics.operations == 1
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-cam-3-axis-persistence-ok")
