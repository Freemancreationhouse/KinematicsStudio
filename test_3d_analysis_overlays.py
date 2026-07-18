from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.workspace import Workspace


workspace = Workspace("3D Analysis Workspace")
mesh = MeshEntity(MeshData.box(10.0, 20.0, 30.0))
workspace.add_3d_entity(mesh)
workspace.selection.select(mesh)

manager = workspace.section_manager
object_bounds, selection_bounds = manager.overlay_bounds(workspace.visible_3d_entities())
assert len(object_bounds) == 1
assert len(selection_bounds) == 1

normal_segments = manager.face_normal_segments(mesh)
assert normal_segments

manager.analysis.face_normals = True
manager.analysis.vertex_display = True
manager.analysis.heatmap_enabled = True
data = manager.to_dict()
restored = Workspace("Restored Analysis Workspace").section_manager
restored.from_dict(data)

assert restored.analysis.face_normals is True
assert restored.analysis.vertex_display is True
assert restored.analysis.heatmap_enabled is True

print("3d-analysis-overlays-ok")
