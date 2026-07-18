from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Inspection Workspace")
manager = workspace.measurement_manager
mesh = MeshEntity(MeshData.box(10.0, 20.0, 30.0))

point = manager.inspect_point(Vector3(1.0, 2.0, 3.0))
edge = manager.inspect_edge(Vector3(), Vector3(0.0, 4.0, 0.0))
face = manager.inspect_face([Vector3(), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)])
stats = manager.mesh_statistics(mesh)
bounds = manager.bounding_box_inspection(mesh)
center = manager.center_of_mass(mesh)
volume = manager.volume_placeholder(mesh)

assert point["type"] == "Point Inspection"
assert edge["length"] == 4.0
assert face["area"] == 0.5
assert stats["vertices"] == 8
assert stats["faces"] == 6
assert bounds["size"].z == 30.0
assert center.z == 0.0
assert volume["value"] is None

print("3d-inspection-tools-ok")
