from engine.bim import (
    BIMElementDefinition,
    BIMInstance,
    ElementParameters,
    ElementRelationships,
)
from engine.commands import (
    AddBIMElementDefinitionCommand,
    AddBIMObjectCommand,
    CreateBIMProjectCommand,
    UpdateBIMElementParametersCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Element BIM"))
definition = BIMElementDefinition("Door", "Door Element")
workspace.command_manager.execute(AddBIMElementDefinitionCommand(workspace, definition))

assert definition in workspace.bim_manager.active_project.element_definitions

instance = BIMInstance("Command Door")
instance.element_definition_id = definition.id
workspace.command_manager.execute(AddBIMObjectCommand(workspace, instance))

before_parameters = instance.element_parameters.to_dict()
before_relationships = instance.element_relationships.to_dict()
after_parameters = ElementParameters("Command Door", "Door", "Door", "Type A", "Wood", "60min").to_dict()
after_relationships = ElementRelationships(hosts=["wall-1"], children=["handle-1"]).to_dict()
workspace.command_manager.execute(
    UpdateBIMElementParametersCommand(
        workspace,
        instance,
        before_parameters,
        after_parameters,
        before_relationships,
        after_relationships,
    )
)

assert instance.element_parameters.material == "Wood"
assert instance.element_relationships.hosts == ["wall-1"]
workspace.command_manager.undo()
assert instance.element_parameters.material == ""
assert instance.element_relationships.hosts == []
workspace.command_manager.redo()
assert instance.element_parameters.fire_rating == "60min"

workspace.command_manager.undo()
workspace.command_manager.undo()
assert instance not in workspace.bim_manager.active_project.instances
workspace.command_manager.redo()
assert instance in workspace.bim_manager.active_project.instances

print("3d-bim-element-library-commands-ok")
