from engine.commands import CreatePrimitiveCommand
from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("Primitive Command Workspace")
workspace.create_layer("Primitives", "#44AAFF")
workspace.set_current_layer("Primitives")

command = CreatePrimitiveCommand(
    workspace,
    "cube",
    {"size": 42.0},
    position=Vector3(10.0, 20.0, 30.0),
    display_mode="shaded",
)
preview = command.preview_entity()
assert preview not in workspace.scene3d.entities()
assert preview.primitive_type == "cube"
assert preview.parameters["size"] == 42.0

workspace.command_manager.execute(command)
assert command.entity in workspace.scene3d.entities()
assert command.entity.layer_name == "Primitives"
assert command.entity.selected
assert command.entity.display_mode == "shaded"
assert workspace.command_manager.undo_available

workspace.command_manager.undo()
assert command.entity not in workspace.scene3d.entities()
assert workspace.command_manager.redo_available

workspace.command_manager.redo()
assert command.entity in workspace.scene3d.entities()
assert workspace.selection.first is command.entity

print("3d-primitive-command-ok")
