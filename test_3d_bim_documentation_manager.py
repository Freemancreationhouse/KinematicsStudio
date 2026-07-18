from engine.bim import (
    DocumentationSettings,
    DrawingScale,
    DrawingSheet,
    FloorPlanView,
    GridGroup,
    GridIntersection,
    GridLine,
    GridMetadata,
    Level,
    LevelDefinition,
    LevelGroup,
    ViewMetadata,
    ViewPlacement,
    ViewTemplate,
    ViewportReference,
)
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Documentation BIM")
level = workspace.bim_manager.add_level(Level("Level 01", 0.0, 3.0))
definition = workspace.bim_manager.add_level_definition(
    LevelDefinition("Level 01 Definition", level.id, level.elevation)
)
group = workspace.bim_manager.add_level_group(LevelGroup("Primary Levels", [level.id]))
grid_line_a = workspace.bim_manager.add_grid_line(
    GridLine("A", Vector3(0.0, 0.0, 0.0), Vector3(0.0, 100.0, 0.0), metadata=GridMetadata("Grid A", "A"))
)
grid_line_1 = workspace.bim_manager.add_grid_line(
    GridLine("1", Vector3(0.0, 0.0, 0.0), Vector3(100.0, 0.0, 0.0), metadata=GridMetadata("Grid 1", "1"))
)
intersection = workspace.bim_manager.add_grid_intersection(
    GridIntersection("A-1", Vector3(0.0, 0.0, 0.0), [grid_line_a.id, grid_line_1.id])
)
grid_group = workspace.bim_manager.add_grid_group(GridGroup("Primary Grids", [grid_line_a.id, grid_line_1.id]))
template = workspace.bim_manager.add_view_template(ViewTemplate("Plan Template", "FloorPlan", {"detail": "medium"}))
view = workspace.bim_manager.add_view(
    FloorPlanView("Level 01 Plan", level.id, template.id, ViewMetadata("Floor plan", "Architecture", "1:100"))
)
sheet = DrawingSheet("Ground Floor Sheet", "A-101")
sheet.add_viewport(ViewportReference(view.id, ViewPlacement(10.0, 20.0, 200.0, 140.0), DrawingScale("1:100", 100.0)))
workspace.bim_manager.add_sheet(sheet)
workspace.bim_manager.active_project.documentation_settings = DocumentationSettings("A1", "1:100", "Studio Title Block")

level_stats = workspace.bim_manager.level_manager.statistics()
grid_stats = workspace.bim_manager.grid_manager.statistics()
view_stats = workspace.bim_manager.view_manager.statistics()
sheet_stats = workspace.bim_manager.sheet_manager.statistics()

assert definition.level_id == level.id
assert group.level_ids == [level.id]
assert intersection.grid_line_ids == [grid_line_a.id, grid_line_1.id]
assert grid_group.grid_line_ids == [grid_line_a.id, grid_line_1.id]
assert level_stats["definitions"] == 1
assert grid_stats.grid_lines == 2
assert grid_stats.intersections == 1
assert view_stats.views == 1
assert view_stats.templates == 1
assert sheet_stats["sheets"] == 1
assert sheet.viewport_references[0].view_id == view.id
assert workspace.bim_manager.view_for(view.id) is view

print("3d-bim-documentation-manager-ok")
