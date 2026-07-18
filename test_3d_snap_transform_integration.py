from engine.commands import TranslateEntity3DCommand
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Snap Transform Workspace")
source = MeshEntity(MeshData.box(10, 10, 10))
target = MeshEntity(MeshData.box(10, 10, 10))
target.set_transform_state(position=Vector3(50.0, 0.0, 0.0))
workspace.add_3d_entity(source)
workspace.add_3d_entity(target)

snap = workspace.snap_manager3d
snap.active_snap = type("Snap", (), {"point": Vector3(50.0, 0.0, 0.0)})()

command = TranslateEntity3DCommand(
    workspace,
    [source],
    Vector3(7.0, 8.0, 9.0),
)
workspace.command_manager.execute(command)
assert source.position3d.x == 50.0
assert source.position3d.y == 0.0

workspace.command_manager.undo()
assert source.position3d.x == 0.0

workspace.command_manager.redo()
assert source.position3d.x == 50.0

print("3d-snap-transform-integration-ok")
