from engine.geometry import Vector3
from engine.scene_organization import ViewFilter
from engine.workspace import Workspace


workspace = Workspace("3D Annotation Filter Workspace")
annotation = workspace.annotation_manager3d.text_note("Filtered Note", Vector3())
collection = workspace.scene_collection_manager.create("Annotation Collection")
workspace.scene_collection_manager.move_entity(annotation, collection)

assert annotation in workspace.visible_annotations3d()

collection.visible = False
assert annotation not in workspace.visible_annotations3d()

collection.visible = True
workspace.view_filter_manager.add(ViewFilter("Hide Annotations", entity_types=["MeshEntity"]))
assert annotation not in workspace.visible_annotations3d()

workspace.view_filter_manager.filters.clear()
workspace.view_filter_manager.add(ViewFilter("Annotation Filter", entity_types=["Annotation3D"]))
assert annotation in workspace.visible_annotations3d()

print("3d-annotation-filter-collection-ok")
