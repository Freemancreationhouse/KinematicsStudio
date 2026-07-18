import os
import tempfile

from engine.bim import (
    DocumentationSettings,
    DrawingSheet,
    FloorPlanView,
    GridIntersection,
    GridLine,
    Level,
    LevelDefinition,
    ViewPlacement,
    ViewTemplate,
    ViewportReference,
)
from engine.cad.application import CADApplication
from engine.geometry import Vector3


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Documentation BIM")
level = workspace.bim_manager.add_level(Level("Persisted Level", 6.0))
workspace.bim_manager.add_level_definition(LevelDefinition("Persisted Level Definition", level.id, 6.0))
grid_line = workspace.bim_manager.add_grid_line(
    GridLine("Persisted Grid", Vector3(0.0, 0.0, 6.0), Vector3(100.0, 0.0, 6.0))
)
workspace.bim_manager.add_grid_intersection(GridIntersection("Persisted Intersection", Vector3(0.0, 0.0, 6.0), [grid_line.id]))
template = workspace.bim_manager.add_view_template(ViewTemplate("Persisted Template", "FloorPlan"))
view = workspace.bim_manager.add_view(FloorPlanView("Persisted Plan", level.id, template.id, location=Vector3(20.0, 0.0, 6.0)))
sheet = DrawingSheet("Persisted Sheet", "A-301", "Persisted Title Block")
sheet.add_viewport(ViewportReference(view.id, ViewPlacement(5.0, 10.0, 150.0, 100.0)))
workspace.bim_manager.add_sheet(sheet)
workspace.bim_manager.active_project.documentation_settings = DocumentationSettings("A2", "1:75", "Persisted Title Block")
workspace.selection.select(view)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_documentation.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_view = project.views[0]
    restored_sheet = project.sheets[0]

    assert project.level_definitions[0].level_id == project.levels[0].id
    assert project.grid_lines[0].name == "Persisted Grid"
    assert project.grid_intersections[0].grid_line_ids == [project.grid_lines[0].id]
    assert project.view_templates[0].name == "Persisted Template"
    assert restored_view.name == "Persisted Plan"
    assert restored_view.selected is True
    assert restored_sheet.viewport_references[0].view_id == restored_view.id
    assert project.documentation_settings.default_sheet_size == "A2"
    assert project.documentation_settings.default_scale == "1:75"

print("3d-bim-documentation-persistence-ok")
