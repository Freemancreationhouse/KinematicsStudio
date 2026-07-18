from engine.bim import BIMSettings, BIMInstance, BIMType, BIMCategory, Level
from engine.commands import (
    AddBIMObjectCommand,
    CreateBIMProjectCommand,
    RemoveBIMObjectCommand,
    UpdateBIMSettingsCommand,
)
from engine.entities.entity3d import MeshEntity
from engine.geometry import MeshData
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command BIM"))

assert workspace.bim_manager.active_project.name == "Command BIM"

category = BIMCategory("Generic Models")
bim_type = BIMType("Generic Type", category.id)
level = Level("Command Level", 3.0, 3.5)
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Command BIM Mesh")
mesh.id = "command-bim-mesh"
workspace.add_3d_entity(mesh)
instance = BIMInstance("Command Instance", category.id, bim_type.id, mesh)

for item in (category, bim_type, level, instance):
    workspace.command_manager.execute(AddBIMObjectCommand(workspace, item))

assert level in workspace.bim_manager.active_project.levels
assert instance in workspace.bim_manager.active_project.instances

workspace.command_manager.undo()
assert instance not in workspace.bim_manager.active_project.instances
workspace.command_manager.redo()
assert instance in workspace.bim_manager.active_project.instances

before = workspace.bim_manager.active_project.settings
after = BIMSettings("millimeters", 4.2, 6.0, "Structure", "Uniclass")
workspace.command_manager.execute(UpdateBIMSettingsCommand(workspace, before, after))
assert workspace.bim_manager.active_project.settings.units == "millimeters"
workspace.command_manager.undo()
assert workspace.bim_manager.active_project.settings.units == before.units

workspace.command_manager.execute(RemoveBIMObjectCommand(workspace, level))
assert level not in workspace.bim_manager.active_project.levels
workspace.command_manager.undo()
assert level in workspace.bim_manager.active_project.levels

print("3d-bim-foundation-commands-ok")
