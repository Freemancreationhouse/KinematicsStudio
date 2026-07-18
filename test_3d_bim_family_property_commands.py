from engine.bim import (
    BIMCategory,
    BIMFamily,
    BIMType,
    PropertyDefinition,
    PropertySet,
    PropertyValue,
)
from engine.commands import (
    AddBIMFamilyCommand,
    AddBIMPropertySetCommand,
    AddBIMTypeCommand,
    CreateBIMProjectCommand,
    UpdateBIMPropertySetCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Family BIM"))
category = workspace.bim_manager.add_category(BIMCategory("Doors"))
family = BIMFamily("Door Family", category.id)
workspace.command_manager.execute(AddBIMFamilyCommand(workspace, family))

bim_type = BIMType("Single Flush", category.id)
bim_type.family_id = family.id
workspace.command_manager.execute(AddBIMTypeCommand(workspace, bim_type))

property_set = PropertySet("Pset_DoorCommon", bim_type.id, "Pset_DoorCommon")
definition = PropertyDefinition("IsExternal", "Boolean")
property_set.add_property(definition, PropertyValue(definition.id, False, "IFC"))
workspace.command_manager.execute(AddBIMPropertySetCommand(workspace, property_set))

assert family in workspace.bim_manager.active_project.families
assert bim_type in workspace.bim_manager.active_project.types
assert property_set in workspace.bim_manager.active_project.property_sets
assert property_set.id in bim_type.property_set_ids

before = property_set.to_dict()
property_set.values[0].value = True
after = property_set.to_dict()
property_set.values[0].value = False
workspace.command_manager.execute(UpdateBIMPropertySetCommand(workspace, property_set, before, after))
assert property_set.value_for("IsExternal").value is True
workspace.command_manager.undo()
assert property_set.value_for("IsExternal").value is False
workspace.command_manager.redo()
assert property_set.value_for("IsExternal").value is True

workspace.command_manager.undo()
workspace.command_manager.undo()
assert property_set not in workspace.bim_manager.active_project.property_sets
workspace.command_manager.redo()
assert property_set in workspace.bim_manager.active_project.property_sets

print("3d-bim-family-property-commands-ok")
