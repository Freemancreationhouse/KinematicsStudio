import tempfile
from pathlib import Path

from engine.ai import AIDrawingPlan, AIDrawingResult, AIEngine, TextToCADValidationError
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Drawing Studio Workspace")
ai = AIEngine()
session = ai.create_session("Drawing Studio Session", workspace)

try:
    ai.plan_engineering_drawing("Create a production drawing", workspace, session)
    raise AssertionError("AI Drawing Studio must reject missing parametric CAD models safely")
except TextToCADValidationError:
    pass

design = ai.execute_parametric_design(
    "Create a 3d printable enclosure 120 x 80 x 40 mm wall thickness 2.5 mm",
    workspace,
    session,
)
assert len(workspace.product_manager.parts) == 1
assert len(workspace.product_manager.features) == 1
assert len(workspace.product_manager.parameters) >= 4

plan = ai.plan_engineering_drawing(
    "Create an ISO production drawing with section and detail views for 3d printing",
    workspace,
    session,
    "ISO",
)
assert isinstance(plan, AIDrawingPlan)
assert plan.validation.valid
assert plan.standard == "ISO"
assert len(plan.sheets) == 1
assert len(plan.views) >= 5
assert any(view.view_type == "Section" for view in plan.views)
assert any(view.view_type == "Detail" for view in plan.views)
assert len(plan.dimensions) >= 4
assert len(plan.annotations) >= 4
assert plan.associativity["model_id"] == workspace.product_manager.parts[-1].id
assert plan.associativity["model_references"]["parameter_ids"]
assert len(workspace.bim_manager.ensure_project().sheets) == 0
assert len(workspace.product_manager.product_reports) == 0

result = ai.execute_engineering_drawing(
    "Create an ISO production drawing with section and detail views for 3d printing",
    workspace,
    session,
    "ISO",
)
assert isinstance(result, AIDrawingResult)
project = workspace.bim_manager.active_project
assert project is not None
assert len(project.views) == len(result.plan.views)
assert len(project.sheets) == 1
assert len(project.sheets[0].viewport_references) == len(result.plan.views)
assert all(view.viewed_entity_ids for view in project.views)
assert len(workspace.product_manager.product_reports) == 1

report = workspace.product_manager.product_reports[0]
assert report.metadata.report_type == "AI Drawing Studio"
assert report.target_id == result.plan.model_id
assert report.metadata.properties["drawing_plan"]["associativity"]["model_id"] == result.plan.model_id
assert report.metadata.properties["drawing_plan"]["dimensions"]
assert report.metadata.properties["drawing_plan"]["annotations"]
assert workspace.command_manager.undo_count == 2

workspace.command_manager.undo()
assert len(workspace.bim_manager.active_project.views) == 0
assert len(workspace.bim_manager.active_project.sheets) == 0
assert len(workspace.product_manager.product_reports) == 0
assert len(workspace.product_manager.parts) == 1

workspace.command_manager.redo()
assert len(workspace.bim_manager.active_project.views) == len(result.plan.views)
assert len(workspace.bim_manager.active_project.sheets) == 1
assert len(workspace.product_manager.product_reports) == 1

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "ai_drawing_studio.ksproj"
    ProjectSerializer().save(workspace, path)
    restored = ProjectSerializer().load(path)
    restored_project = restored.bim_manager.active_project
    restored_report = restored.product_manager.product_reports[0]
    assert len(restored_project.views) == len(result.plan.views)
    assert len(restored_project.sheets) == 1
    assert len(restored_project.sheets[0].viewport_references) == len(result.plan.views)
    assert restored_report.metadata.report_type == "AI Drawing Studio"
    assert restored_report.metadata.properties["drawing_plan"]["associativity"]["model_id"] == result.plan.model_id

diagnostics = ai.diagnostics()["drawing_studio"]
assert diagnostics["successful"] == 1
assert diagnostics["failed"] == 1
assert diagnostics["views_generated"] == len(result.plan.views)
assert diagnostics["dimensions_generated"] == len(result.plan.dimensions)
assert diagnostics["annotations_generated"] == len(result.plan.annotations)
assert diagnostics["validation_statistics"] == 1
assert diagnostics["associativity_statistics"] >= 2

print("ai-drawing-studio-ok")
