from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.picking3d import PickingManager3D
from engine.workspace import Workspace
from engine.render import Camera3D


workspace = Workspace("3D Snap Precision Workspace")
entity = MeshEntity(MeshData.box(100, 100, 100))
workspace.add_3d_entity(entity)

camera = Camera3D()
camera.resize(640, 480)
center = entity.bounding_box3d.center
screen = camera.project(center)
assert screen is not None

ray = camera.screen_ray(screen[0], screen[1])
hit = PickingManager3D().pick(workspace, ray)
assert hit is not None

snap = workspace.snap_manager3d
snap.filters = {"VERTEX", "OBJECT_CENTER", "NEAREST"}
result = snap.snap_ray(workspace, ray, camera)
assert result is not None
assert result.mode in snap.DEFAULT_FILTERS
assert snap.highlighted_entity is not None

snap.tolerance = 0.0001
miss = snap.snap_ray(workspace, camera.screen_ray(0, 0), camera)
assert miss is None

print("3d-snap-precision-ok")
