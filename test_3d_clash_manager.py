from engine.clashes import ClashSettings
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.references3d import ReferenceTransform
from engine.workspace.workspace import Workspace


workspace = Workspace()
ref_a = workspace.reference_manager.create_model("A", "a.obj", category="Architecture")
ref_b = workspace.reference_manager.create_model("B", "b.obj", category="Structure")
workspace.reference_manager.create_instance(ref_a, ReferenceTransform(Vector3()))
workspace.reference_manager.create_instance(ref_b, ReferenceTransform(Vector3(10.0, 0.0, 0.0)))

results = workspace.clash_manager.detect(workspace)
assert results
assert results[0].clash_type == "Reference Clash"

workspace.clash_manager.set_results(results)
assert workspace.clash_manager.statistics.reference >= 1
assert workspace.visible_clashes() == results

workspace.clash_manager.settings = ClashSettings(clearance=5.0, include_references=False)
mesh_a = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Native A")
mesh_b = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Native B")
mesh_b.set_transform_state(position=Vector3(12.0, 0.0, 0.0))
workspace.add_3d_entity(mesh_a)
workspace.add_3d_entity(mesh_b)
results = workspace.clash_manager.detect(workspace, workspace.clash_manager.settings)
assert results[0].clash_type == "Clearance Clash"

workspace.clash_manager.settings = ClashSettings(include_references=False)
mesh_b.set_transform_state(position=Vector3())
results = workspace.clash_manager.detect(workspace, workspace.clash_manager.settings)
assert any(result.clash_type == "Duplicate Geometry" for result in results)

workspace.clash_manager.settings = ClashSettings(category_filter="Architecture")
results = workspace.clash_manager.detect(workspace, workspace.clash_manager.settings)
assert results == []

print("3d-clash-manager-ok")
