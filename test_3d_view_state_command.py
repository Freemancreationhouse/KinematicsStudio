from engine.commands import (
    DeleteViewStateCommand,
    RenameViewStateCommand,
    RestoreViewStateCommand,
    SaveViewStateCommand,
    SetDisplayModeCommand,
    SetVisualStyleCommand,
)
from engine.render import Camera3D
from engine.view_states import VisualStyle
from engine.workspace import Workspace


workspace = Workspace("3D View Command Workspace")
camera = Camera3D()
camera.state.yaw = 10.0
workspace.visual_style_manager.add(VisualStyle("Command Style"))

workspace.command_manager.execute(SaveViewStateCommand(workspace, "Saved", camera))
assert workspace.view_state_manager.get("Saved") is not None

workspace.command_manager.undo()
assert workspace.view_state_manager.get("Saved") is None

workspace.command_manager.redo()
assert workspace.view_state_manager.get("Saved") is not None

workspace.command_manager.execute(RenameViewStateCommand(workspace, "Saved", "Renamed"))
assert workspace.view_state_manager.get("Renamed") is not None
workspace.command_manager.undo()
assert workspace.view_state_manager.get("Saved") is not None

camera.state.yaw = 80.0
workspace.command_manager.execute(RestoreViewStateCommand(workspace, "Saved", camera))
assert camera.state.yaw == 10.0
workspace.command_manager.undo()
assert camera.state.yaw == 80.0

workspace.command_manager.execute(SetDisplayModeCommand(workspace, "bounding_box"))
assert workspace.display_mode_manager.current_mode == "bounding_box"
workspace.command_manager.undo()
assert workspace.display_mode_manager.current_mode == "wireframe"

workspace.command_manager.execute(SetVisualStyleCommand(workspace, "Command Style"))
assert workspace.visual_style_manager.current.name == "Command Style"
workspace.command_manager.undo()
assert workspace.visual_style_manager.current.name == "Default"

workspace.command_manager.execute(DeleteViewStateCommand(workspace, "Saved"))
assert workspace.view_state_manager.get("Saved") is None
workspace.command_manager.undo()
assert workspace.view_state_manager.get("Saved") is not None

print("3d-view-state-command-ok")
