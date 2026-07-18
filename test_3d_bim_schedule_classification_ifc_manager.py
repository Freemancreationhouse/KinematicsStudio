from engine.bim import (
    BIMElementDefinition,
    BIMInstance,
    ClassificationCode,
    ClassificationMapping,
    ClassificationMetadata,
    ClassificationSystem,
    IFCElement,
    IFCProject,
    ScheduleDefinition,
    ScheduleField,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Schedule Classification IFC BIM")
definition = workspace.bim_manager.add_element_definition(BIMElementDefinition("Door", "Door"))
door = BIMInstance("Door 101")
door.element_definition_id = definition.id
workspace.bim_manager.add_instance(door)

schedule = ScheduleDefinition("Door Schedule", "Door")
schedule.add_field(ScheduleField("Name", "name"))
schedule.add_field(ScheduleField("Category", "category"))
workspace.bim_manager.add_schedule(schedule)
workspace.bim_manager.build_schedule(schedule)

system = ClassificationSystem(
    "OmniClass",
    ClassificationMetadata("OmniClass placeholder", "OmniClass", "Future"),
)
code = system.add_code(ClassificationCode("23-17 11 00", "Doors"))
workspace.bim_manager.add_classification_system(system)
mapping = workspace.bim_manager.add_classification_mapping(
    ClassificationMapping(door.id, system.id, code.code, code.id)
)

ifc_project = workspace.bim_manager.add_ifc_item(IFCProject("IFC BIM", workspace.bim_manager.active_project.id))
ifc_element = workspace.bim_manager.add_ifc_item(
    IFCElement("IFC Door", door.id, door.mesh_entity_id, "IfcDoor")
)

stats = workspace.bim_manager.schedule_manager.statistics()
classification_stats = workspace.bim_manager.classification_manager.statistics()
ifc_stats = workspace.bim_manager.ifc_manager.statistics()

assert schedule.rows[0].source_id == door.id
assert schedule.rows[0].values["Category"] == "Door"
assert stats.schedules == 1
assert classification_stats.systems == 1
assert classification_stats.codes == 1
assert classification_stats.mappings == 1
assert workspace.bim_manager.classifications_for(door) == [mapping]
assert workspace.bim_manager.schedules_for(door) == [schedule]
assert workspace.bim_manager.ifc_status_for(door) == "Linked"
assert ifc_project.bim_project_id == workspace.bim_manager.active_project.id
assert ifc_element.ifc_type == "IfcDoor"
assert ifc_stats["elements"] == 1

print("3d-bim-schedule-classification-ifc-manager-ok")
