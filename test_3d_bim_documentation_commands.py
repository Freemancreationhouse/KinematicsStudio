from engine.bim import DocumentationSettings, DrawingSheet, FloorPlanView, Level, LevelDefinition
from engine.commands import (
    AddBIMObjectCommand,
    AddBIMSheetCommand,
    AddBIMViewCommand,
    CreateBIMProjectCommand,
    UpdateBIMDocumentationSettingsCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Documentation BIM"))
level = Level("Command Level", 3.0)
workspace.command_manager.execute(AddBIMObjectCommand(workspace, level))
definition = LevelDefinition("Command Level Definition", level.id, level.elevation)
workspace.command_manager.execute(AddBIMObjectCommand(workspace, definition))
view = FloorPlanView("Command Plan", level.id)
workspace.command_manager.execute(AddBIMViewCommand(workspace, view))
sheet = DrawingSheet("Command Sheet", "A-201")
workspace.command_manager.execute(AddBIMSheetCommand(workspace, sheet))

project = workspace.bim_manager.active_project
assert level in project.levels
assert definition in project.level_definitions
assert view in project.views
assert sheet in project.sheets

before = project.documentation_settings
after = DocumentationSettings("A0", "1:50", "Command Title Block")
workspace.command_manager.execute(UpdateBIMDocumentationSettingsCommand(workspace, before, after))
assert project.documentation_settings.default_sheet_size == "A0"
workspace.command_manager.undo()
assert project.documentation_settings.default_sheet_size == before.default_sheet_size
workspace.command_manager.redo()
assert project.documentation_settings.title_block == "Command Title Block"

workspace.command_manager.undo()
workspace.command_manager.undo()
assert sheet not in project.sheets
workspace.command_manager.redo()
assert sheet in project.sheets

print("3d-bim-documentation-commands-ok")
