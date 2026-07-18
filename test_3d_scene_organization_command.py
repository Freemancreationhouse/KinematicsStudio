from engine.commands import (
    AddViewFilterCommand,
    CreateSceneCollectionCommand,
    MoveEntityToCollectionCommand,
    RenameSceneCollectionCommand,
    RestoreDisplayPresetCommand,
    SaveDisplayPresetCommand,
    UpdateSceneCollectionCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.scene_organization import ViewFilter
from engine.workspace import Workspace


workspace = Workspace("3D Organization Command Workspace")
mesh = MeshEntity(MeshData.box(10.0, 10.0, 10.0), name="Command Mesh")
workspace.add_3d_entity(mesh)

workspace.command_manager.execute(CreateSceneCollectionCommand(workspace, "Commands"))
collection = workspace.scene_collection_manager.get("Commands")
assert collection is not None

workspace.command_manager.execute(MoveEntityToCollectionCommand(workspace, mesh, collection))
assert workspace.scene_collection_manager.entity_collection(mesh) is collection
workspace.command_manager.undo()
assert workspace.scene_collection_manager.entity_collection(mesh) is None
workspace.command_manager.redo()

workspace.command_manager.execute(RenameSceneCollectionCommand(workspace, collection, "Renamed Commands"))
assert workspace.scene_collection_manager.get("Renamed Commands") is not None
workspace.command_manager.undo()
assert workspace.scene_collection_manager.get("Commands") is not None

workspace.command_manager.execute(
    UpdateSceneCollectionCommand(collection, {"visible": True}, {"visible": False})
)
assert collection.visible is False
workspace.command_manager.undo()
assert collection.visible is True

view_filter = ViewFilter("Command Filter", entity_types=["MeshEntity"])
workspace.command_manager.execute(AddViewFilterCommand(workspace, view_filter))
assert workspace.view_filter_manager.get("Command Filter") is view_filter

workspace.display_mode_manager.set_mode("x_ray")
workspace.command_manager.execute(SaveDisplayPresetCommand(workspace, "Command Preset"))
assert workspace.display_preset_manager.get("Command Preset") is not None
workspace.display_mode_manager.set_mode("wireframe")
workspace.command_manager.execute(RestoreDisplayPresetCommand(workspace, "Command Preset"))
assert workspace.display_mode_manager.current_mode == "x_ray"

print("3d-scene-organization-command-ok")
