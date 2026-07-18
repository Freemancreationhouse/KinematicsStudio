from engine.geometry import Vector3
from engine.tools import CubePrimitiveTool
from engine.workspace import Workspace


workspace = Workspace("3D Snap Primitive Workspace")
workspace.snap_manager3d.grid_spacing = 25.0
workspace.snap_manager3d.filters = {"GRID"}

tool = CubePrimitiveTool()
tool.mouse_move(workspace, Vector3(26.0, 49.0, 2.0))
assert tool.preview is not None
assert tool.preview.position3d.x == 25.0
assert tool.preview.position3d.y == 50.0
assert tool.preview.position3d.z == 0.0

tool.mouse_press(workspace, Vector3(26.0, 49.0, 2.0))
entity = workspace.scene3d.entities()[0]
assert entity.position3d.x == 25.0
assert entity.position3d.y == 50.0
assert entity.position3d.z == 0.0

print("3d-snap-primitive-placement-ok")
