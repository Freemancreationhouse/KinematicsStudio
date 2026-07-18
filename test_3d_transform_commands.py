from engine.commands import (
    RotateEntity3DCommand,
    ScaleEntity3DCommand,
    TranslateEntity3DCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Transform Command Workspace")
first = MeshEntity(MeshData.box(10, 10, 10))
second = MeshEntity(MeshData.box(20, 10, 10))
workspace.add_3d_entity(first)
workspace.add_3d_entity(second)
workspace.selection.select_many([first, second])

translate = TranslateEntity3DCommand(
    workspace,
    workspace.selection.selected,
    Vector3(10.0, 20.0, 30.0),
    axis="X",
)
workspace.command_manager.execute(translate)
assert first.position3d.x == 10.0
assert first.position3d.y == 0.0
assert second.position3d.x == 10.0

workspace.command_manager.undo()
assert first.position3d.x == 0.0
assert second.position3d.x == 0.0

workspace.command_manager.redo()
assert first.position3d.x == 10.0
assert second.position3d.x == 10.0

rotate = RotateEntity3DCommand(
    workspace,
    [first, second],
    Vector3(15.0, 25.0, 35.0),
    axis="Z",
)
workspace.command_manager.execute(rotate)
assert first.rotation3d.z == 35.0
assert first.rotation3d.x == 0.0

scale = ScaleEntity3DCommand(
    workspace,
    [first, second],
    Vector3(2.0, 3.0, 4.0),
    axis="Y",
)
workspace.command_manager.execute(scale)
assert first.scale3d.y == 3.0
assert first.scale3d.x == 1.0

preview = ScaleEntity3DCommand(
    workspace,
    [first],
    Vector3(2.0, 2.0, 2.0),
).preview_states()
assert preview[0]["entity"] is first
assert first.scale3d.y == 3.0

print("3d-transform-commands-ok")
