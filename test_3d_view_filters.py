from engine.entities import Line3D, MeshEntity
from engine.geometry import MeshData, Vector3
from engine.scene_organization import ViewFilter
from engine.sections import SectionPlane
from engine.workspace import Workspace


workspace = Workspace("3D Filter Workspace")
line = Line3D(Vector3(), Vector3(10.0, 0.0, 0.0), name="Filter Line")
mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Filter Mesh")
workspace.add_3d_entity(line)
workspace.add_3d_entity(mesh)

collection = workspace.scene_collection_manager.create("Filtered Collection")
workspace.scene_collection_manager.move_entity(mesh, collection)

type_filter = ViewFilter("Meshes Only", entity_types=["MeshEntity"])
workspace.view_filter_manager.add(type_filter)
assert mesh in workspace.visible_3d_entities()
assert line not in workspace.visible_3d_entities()

workspace.view_filter_manager.filters.clear()
collection_filter = ViewFilter("Collection Only", collection_names=["Filtered Collection"])
workspace.view_filter_manager.add(collection_filter)
assert workspace.view_filter_manager.matches(mesh, workspace)
assert not workspace.view_filter_manager.matches(line, workspace)

measurement = workspace.measurement_manager.point_to_point(Vector3(), Vector3(1.0, 0.0, 0.0))
workspace.measurement_manager.add(measurement)
section = SectionPlane("Filter Section")
workspace.section_manager.add(section)
workspace.view_filter_manager.filters.clear()
workspace.view_filter_manager.add(
    ViewFilter("Hide Analysis", include_measurements=False, include_sections=False)
)
assert measurement not in workspace.visible_measurements()
assert section not in workspace.visible_sections()

print("3d-view-filters-ok")
