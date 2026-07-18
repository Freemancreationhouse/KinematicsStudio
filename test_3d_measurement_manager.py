from engine.entities import MeshEntity, Polyline3D
from engine.geometry import MeshData, Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Measurement Workspace")
manager = workspace.measurement_manager

distance = manager.point_to_point(Vector3(), Vector3(3.0, 4.0, 0.0))
assert distance.result.value == 5.0

edge = manager.edge_length(Vector3(), Vector3(0.0, 0.0, 7.0))
assert edge.result.value == 7.0

polyline = manager.polyline_length([
    Vector3(),
    Vector3(3.0, 0.0, 0.0),
    Vector3(3.0, 4.0, 0.0),
])
assert polyline.result.value == 7.0

area = manager.surface_area([
    Vector3(),
    Vector3(10.0, 0.0, 0.0),
    Vector3(0.0, 10.0, 0.0),
])
assert area.result.value == 50.0

mesh = MeshEntity(MeshData.box(10.0, 20.0, 30.0))
mesh_area = manager.mesh_area(mesh)
assert mesh_area.result.value > 0.0

bounds = manager.bounding_box_size(mesh)
assert bounds.result.value["x"] == 10.0
assert bounds.result.value["y"] == 20.0
assert bounds.result.value["z"] == 30.0

radius = manager.radius(Vector3(), Vector3(5.0, 0.0, 0.0))
diameter = manager.diameter(Vector3(), Vector3(5.0, 0.0, 0.0))
assert radius.result.value == 5.0
assert diameter.result.value == 10.0

angle = manager.angle(Vector3(), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))
assert round(angle.result.value) == 90

delta = manager.xyz_delta(Vector3(1.0, 2.0, 3.0), Vector3(4.0, 6.0, 9.0))
assert delta.result.value == {"x": 3.0, "y": 4.0, "z": 6.0}

first = Polyline3D([Vector3(), Vector3(10.0, 0.0, 0.0)])
second = Polyline3D([Vector3(2.0, 0.0, 0.0), Vector3(20.0, 0.0, 0.0)])
minimum = manager.minimum_distance(first, second)
maximum = manager.maximum_distance(first, second)
assert minimum.result.value == 2.0
assert maximum.result.value == 20.0

print("3d-measurement-manager-ok")
