from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Snap Workspace")
entity = MeshEntity(MeshData.box(100, 80, 60))
workspace.add_3d_entity(entity)

snap = workspace.snap_manager3d
candidates = snap.candidate_points(workspace)
modes = {candidate.mode for candidate in candidates}

assert "VERTEX" in modes
assert "EDGE" in modes
assert "FACE_CENTER" in modes
assert "FACE_CORNER" in modes
assert "FACE_MIDPOINT" in modes
assert "OBJECT_CENTER" in modes
assert "ORIGIN" in modes
assert "AXIS" in modes
assert "NEAREST" in modes

snap.set_filter("VERTEX", False)
assert "VERTEX" not in {candidate.mode for candidate in snap.candidate_points(workspace)}

snap.set_filter("VERTEX", True)
point = snap.snap_point(workspace, Vector3(2.0, 1.0, 0.0))
assert point.distance_to(Vector3()) <= snap.world_tolerance
assert snap.active_snap is not None
assert snap.active_snap.mode in ("ORIGIN", "OBJECT_CENTER", "NEAREST")

snap.set_enabled(False)
free_point = snap.snap_point(workspace, Vector3(3.0, 4.0, 5.0))
assert free_point.x == 3.0
assert snap.active_snap is None

print("3d-snap-manager-ok")
