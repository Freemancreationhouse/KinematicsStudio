from engine.bim import (
    BIMElementDefinition,
    BIMInstance,
    ClassificationCode,
    ClassificationMapping,
    ClassificationSystem,
    IFCElement,
    ScheduleDefinition,
    ScheduleField,
)
from engine.commands import (
    AddBIMClassificationCommand,
    AddBIMElementDefinitionCommand,
    AddBIMIFCObjectCommand,
    AddBIMObjectCommand,
    AddBIMScheduleCommand,
    BuildBIMScheduleCommand,
    CreateBIMProjectCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Batch F BIM"))

definition = BIMElementDefinition("Window", "Window")
workspace.command_manager.execute(AddBIMElementDefinitionCommand(workspace, definition))

window = BIMInstance("Window 201")
window.element_definition_id = definition.id
workspace.command_manager.execute(AddBIMObjectCommand(workspace, window))

schedule = ScheduleDefinition("Window Schedule", "Window")
schedule.add_field(ScheduleField("Name", "name"))
workspace.command_manager.execute(AddBIMScheduleCommand(workspace, schedule))
workspace.command_manager.execute(BuildBIMScheduleCommand(workspace, schedule))
assert len(schedule.rows) == 1

system = ClassificationSystem("UniClass")
code = system.add_code(ClassificationCode("EF_25_10", "Windows"))
workspace.command_manager.execute(AddBIMClassificationCommand(workspace, system))
mapping = ClassificationMapping(window.id, system.id, code.code, code.id)
workspace.command_manager.execute(AddBIMClassificationCommand(workspace, mapping))
assert workspace.bim_manager.classifications_for(window) == [mapping]

ifc_element = IFCElement("IFC Window", window.id, window.mesh_entity_id, "IfcWindow")
workspace.command_manager.execute(AddBIMIFCObjectCommand(workspace, ifc_element))
assert workspace.bim_manager.ifc_status_for(window) == "Linked"

workspace.command_manager.undo()
assert workspace.bim_manager.ifc_status_for(window) == "Unmapped"
workspace.command_manager.redo()
assert workspace.bim_manager.ifc_status_for(window) == "Linked"

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.bim_manager.classifications_for(window) == []
workspace.command_manager.redo()
assert workspace.bim_manager.classifications_for(window) == [mapping]

print("3d-bim-schedule-classification-ifc-commands-ok")
