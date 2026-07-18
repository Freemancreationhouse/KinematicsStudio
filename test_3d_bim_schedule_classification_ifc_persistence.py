import os
import tempfile

from engine.bim import (
    BIMElementDefinition,
    BIMInstance,
    ClassificationCode,
    ClassificationMapping,
    ClassificationSystem,
    IFCElement,
    IFCExportSettings,
    IFCImportSettings,
    ScheduleDefinition,
    ScheduleField,
)
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Batch F BIM")
definition = workspace.bim_manager.add_element_definition(BIMElementDefinition("Room", "Room"))
room = BIMInstance("Room 301")
room.element_definition_id = definition.id
workspace.bim_manager.add_instance(room)

schedule = ScheduleDefinition("Room Schedule", "Room")
schedule.add_field(ScheduleField("Name", "name"))
workspace.bim_manager.add_schedule(schedule)
workspace.bim_manager.build_schedule(schedule)

system = workspace.bim_manager.add_classification_system(ClassificationSystem("MasterFormat"))
code = system.add_code(ClassificationCode("09 00 00", "Finishes"))
workspace.bim_manager.add_classification_mapping(ClassificationMapping(room.id, system.id, code.code, code.id))
workspace.bim_manager.add_ifc_item(IFCElement("IFC Room", room.id, room.mesh_entity_id, "IfcSpace"))
workspace.bim_manager.active_project.ifc_export_settings = IFCExportSettings("IFC4", False, True, {"profile": "coordination"})
workspace.bim_manager.active_project.ifc_import_settings = IFCImportSettings("IFC4", True, True, {"mode": "metadata"})
workspace.selection.select(room)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_batch_f.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_room = project.instances[0]

    assert project.schedules[0].rows[0].source_id == restored_room.id
    assert project.classification_systems[0].codes[0].code == "09 00 00"
    assert project.classification_mappings[0].target_id == restored_room.id
    assert project.ifc_elements[0].ifc_type == "IfcSpace"
    assert project.ifc_export_settings.options["profile"] == "coordination"
    assert project.ifc_import_settings.options["mode"] == "metadata"
    assert restored_room.selected is True
    assert restored_workspace.bim_manager.ifc_status_for(restored_room) == "Linked"

print("3d-bim-schedule-classification-ifc-persistence-ok")
