from engine.bim import BIMParametricDefinition, BIMView, DrawingSheet
from engine.commands import (
    AddBIMAnnotationCommand,
    AddBIMCoordinationReferenceCommand,
    AddBIMSheetCommand,
    AddBIMViewCommand,
    CreateBIMDocumentationDocumentCommand,
    CreateWallCommand,
    ExportIFC43Command,
    GenerateBIMDrawingCommand,
    GenerateBIMScheduleCommand,
    ImportIFC43Command,
    PublishBIMPackageCommand,
    RunBIMDocumentationTakeoffCommand,
    UpdateIFC43Command,
    ValidateBIMDocumentationCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.bim_manager
manager.initialize("Release 1.9 IFC Documentation", project_units="meters")

project_node = manager.create_spatial_element("Project", "Documentation Project")
site = manager.create_spatial_element("Site", "Main Site", project_node.id)
building = manager.create_spatial_element("Building", "Tower A", site.id)
level = manager.create_spatial_element("Building Storey", "Level 01", building.id)

wall_type = manager.create_native_element_type(
    "Wall Type 200",
    "Wall",
    "Architecture",
    material_id="mat-concrete",
    parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=8.0),
)

workspace.command_manager.execute(
    CreateWallCommand(
        workspace,
        "Documentation Wall",
        [{"body_id": "body-doc-wall", "body_name": "Parametric wall body", "source": "BodyManager"}],
        element_type_id=wall_type.id,
        material_assignment_id="mat-concrete",
        level_id=level.id,
        parameters=BIMParametricDefinition(thickness=0.2, height=3.2, length=8.0),
    )
)
wall = manager.active_project.native_elements[-1]

view = BIMView("Level 01 Plan", level.id)
view.view_type = "Plan"
view.viewed_entity_ids = [wall.id]
sheet = DrawingSheet("Sheet A101", "A101", "Studio Title Block")
workspace.command_manager.execute(AddBIMViewCommand(workspace, view))
workspace.command_manager.execute(AddBIMSheetCommand(workspace, sheet))

workspace.command_manager.execute(ExportIFC43Command(workspace, [wall.id]))
ifc_export = manager.active_project.ifc_exchange_records[-1]
assert "IFC4X3" in ifc_export.content
assert ifc_export.global_id_map[wall.id] == wall.global_id

workspace.command_manager.execute(ImportIFC43Command(workspace, ifc_export.content))
ifc_import = manager.active_project.ifc_exchange_records[-1]
assert ifc_import.exchange_type == "Import"
assert any(entity.object_id == wall.id for entity in manager.active_project.core_ifc_entities)

workspace.command_manager.execute(UpdateIFC43Command(workspace, ifc_export, [wall.id]))
assert manager.active_project.ifc_exchange_records[-1].exchange_type == "Incremental Update"

workspace.command_manager.execute(
    CreateBIMDocumentationDocumentCommand(
        workspace,
        "Permit Drawing Set",
        "Drawing Set",
        "Studio Title Block",
        revision_metadata={"revision": "A"},
        issue_metadata={"issued_for": "Coordination"},
    )
)
document = manager.active_project.documentation_documents[-1]
workspace.command_manager.execute(
    GenerateBIMDrawingCommand(
        workspace,
        "Plan",
        "Level 01 Plan",
        [wall.id],
        sheet.id,
        view.id,
        "1:100",
        viewport_metadata={"viewport": "A101-1"},
        template_metadata={"template": "Architectural Plan"},
    )
)
workspace.command_manager.execute(
    GenerateBIMDrawingCommand(workspace, "Section", "Wall Section", [wall.id], sheet.id, view.id, "1:50")
)
document.sheet_ids.append(sheet.id)
document.view_ids.append(view.id)

workspace.command_manager.execute(
    GenerateBIMScheduleCommand(
        workspace,
        "Wall",
        "Wall Schedule",
        [("Name", "name"), ("Type", "element_type"), ("Level", "level"), ("Length", "length"), ("Material", "material")],
        {"format": "CSV-ready"},
    )
)
schedule = manager.active_project.schedules[-1]
assert schedule.rows and schedule.rows[0].source_id == wall.id

workspace.command_manager.execute(RunBIMDocumentationTakeoffCommand(workspace))
quantity_types = {item.quantity_type for item in manager.active_project.quantity_items}
assert {"Count", "Length", "Area", "Volume", "Material"}.issubset(quantity_types)

workspace.command_manager.execute(AddBIMAnnotationCommand(workspace, "Room Tag", wall.id, "W-001", view.id, sheet.id))
workspace.command_manager.execute(AddBIMAnnotationCommand(workspace, "Dimension", wall.id, "8000", view.id, sheet.id))
workspace.command_manager.execute(
    PublishBIMPackageCommand(
        workspace,
        "Permit PDF Package",
        "PDF",
        [sheet.id],
        export_settings={"dpi": 300},
        revision_metadata={"revision": "A"},
        plot_metadata={"paper": "A1"},
    )
)
workspace.command_manager.execute(
    AddBIMCoordinationReferenceCommand(
        workspace,
        "Linked Structural Model",
        "Linked Model",
        "structural.ksproj",
        [wall.id],
        view_coordination={"view_id": view.id},
        sheet_coordination={"sheet_id": sheet.id},
    )
)
workspace.command_manager.execute(ValidateBIMDocumentationCommand(workspace))

visualization = manager.documentation_visualization_metadata()
validation = manager.active_project.documentation_validation_report
diagnostics = manager.documentation_diagnostics_report()

assert validation.valid, validation.issues
assert diagnostics.ifc_exchanges == 3
assert diagnostics.documents == 1
assert diagnostics.drawings == 2
assert diagnostics.annotations == 2
assert diagnostics.schedules >= 1
assert diagnostics.quantity_items >= 5
assert diagnostics.publishing_packages == 1
assert diagnostics.coordination_references == 1
assert visualization["drawing_previews"]
assert visualization["sheet_previews"]
assert visualization["schedule_previews"][schedule.id]
assert workspace.scene3d.entities() == []
assert workspace.command_manager.undo_count >= 13

workspace.command_manager.undo()
assert manager.active_project.documentation_validation_report is not validation
workspace.command_manager.redo()
assert manager.active_project.documentation_validation_report.valid

persisted = manager.to_dict()
restored = manager.__class__()
restored.from_dict(persisted)
restored_validation = restored.validate_bim_documentation()

assert restored_validation.valid, restored_validation.issues
assert len(restored.active_project.ifc_exchange_records) == 3
assert len(restored.active_project.generated_drawings) == 2
assert len(restored.active_project.documentation_annotations) == 2
assert restored.active_project.publishing_packages[0].sheet_ids == [sheet.id]

print("bim-ifc-documentation-ok")
