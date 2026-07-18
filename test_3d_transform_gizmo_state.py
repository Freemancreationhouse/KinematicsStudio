from engine.geometry import Vector3
from engine.transform_gizmo import TransformGizmo


gizmo = TransformGizmo()
gizmo.set_mode("rotate")
gizmo.set_axis_constraint("X")
assert gizmo.axis_constraint == "X"
assert gizmo.plane_constraint is None

gizmo.set_plane_constraint("YZ")
assert gizmo.plane_constraint == "YZ"
assert gizmo.axis_constraint is None

gizmo.set_coordinate_mode("local")
gizmo.set_pivot_mode("origin")
gizmo.set_pivot(Vector3(1.0, 2.0, 3.0))

data = gizmo.to_dict()
restored = TransformGizmo()
restored.from_dict(data)

assert restored.mode == "rotate"
assert restored.plane_constraint == "YZ"
assert restored.coordinate_mode == "local"
assert restored.pivot_mode == "origin"
assert restored.pivot.x == 1.0
assert restored.pivot.y == 2.0
assert restored.pivot.z == 3.0

print("3d-transform-gizmo-state-ok")
