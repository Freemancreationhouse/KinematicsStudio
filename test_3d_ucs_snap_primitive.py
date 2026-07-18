from engine.geometry import Vector3
from engine.tools import CubePrimitiveTool
from engine.workspace import Workspace


workspace = Workspace("UCS Snap Primitive Workspace")
workspace.coordinate_system_manager.create_ucs(
    "Shifted UCS",
    origin=Vector3(10.0, 0.0, 0.0),
)
workspace.coordinate_system_manager.activate("Shifted UCS")
workspace.coordinate_system_manager.grid_spacing = 25.0
workspace.snap_manager3d.filters = {"GRID"}

tool = CubePrimitiveTool()
tool.mouse_press(workspace, Vector3(36.0, 49.0, 2.0))
entity = workspace.scene3d.entities()[0]

assert entity.position3d.x == 35.0
assert entity.position3d.y == 50.0
assert entity.position3d.z == 0.0

print("3d-ucs-snap-primitive-ok")
