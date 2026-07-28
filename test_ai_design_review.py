import tempfile
from pathlib import Path

from engine.ai import AIDesignReviewPlan, AIDesignReviewResult, AIEngine, TextToCADValidationError
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Design Review Workspace")
ai = AIEngine()
session = ai.create_session("Design Review Session", workspace)

try:
    ai.review_engineering_package("Review the complete package", workspace, session)
    raise AssertionError("AI Design Review must reject missing parametric CAD models safely")
except TextToCADValidationError:
    pass

ai.execute_parametric_design(
    "Create a cnc machined flange diameter 100 mm height 12 mm hole diameter 40 mm with machinability",
    workspace,
    session,
)

try:
    ai.review_engineering_package("Review the complete package", workspace, session)
    raise AssertionError("AI Design Review must reject missing drawings and documentation safely")
except TextToCADValidationError:
    pass

ai.execute_engineering_drawing(
    "Create an ISO production drawing with detail view for cnc machining",
    workspace,
    session,
    "ISO",
)

try:
    ai.review_engineering_package("Review the complete package", workspace, session)
    raise AssertionError("AI Design Review must reject missing documentation safely")
except TextToCADValidationError:
    pass

ai.execute_engineering_documentation(
    "Create ISO manufacturing documentation with BOM assembly instructions inspection plan and revision history",
    workspace,
    session,
    "ISO",
)

before_parts = len(workspace.product_manager.parts)
before_features = len(workspace.product_manager.features)
before_drawings = len(workspace.bim_manager.active_project.sheets)
before_reports = len(workspace.product_manager.product_reports)

plan = ai.review_engineering_package(
    "Review the complete ISO engineering package for manufacturability robustness drawings documentation and risks",
    workspace,
    session,
    "ISO",
)
assert isinstance(plan, AIDesignReviewPlan)
assert plan.review_depth == "Complete Engineering Package"
assert "Parametric Model" in plan.review_scope
assert "Engineering Drawings" in plan.review_scope
assert "Documentation" in plan.review_scope
assert plan.scores.overall > 0
assert plan.scores.engineering > 0
assert plan.recommendations
assert plan.risks
assert plan.summary["overall_quality_score"] == plan.scores.overall
assert plan.associativity["model_references"]["part_ids"]
assert plan.associativity["drawing_references"]
assert plan.associativity["documentation_references"]
assert len(workspace.product_manager.parts) == before_parts
assert len(workspace.product_manager.features) == before_features
assert len(workspace.bim_manager.active_project.sheets) == before_drawings
assert len(workspace.product_manager.product_reports) == before_reports

result = ai.execute_design_review(
    "Review the complete ISO engineering package for manufacturability robustness drawings documentation and risks",
    workspace,
    session,
    "ISO",
)
assert isinstance(result, AIDesignReviewResult)
assert len(workspace.product_manager.parts) == before_parts
assert len(workspace.product_manager.features) == before_features
assert len(workspace.bim_manager.active_project.sheets) == before_drawings
assert len(workspace.product_manager.product_reports) == before_reports + 1
review_report = workspace.product_manager.product_reports[-1]
assert review_report.metadata.report_type == "AI Design Review"
assert review_report.metadata.properties["review_plan"]["scores"]["overall"] == result.plan.scores.overall
assert review_report.metadata.properties["review_plan"]["recommendations"]
assert review_report.metadata.properties["review_plan"]["risks"]
assert review_report.metadata.properties["review_plan"]["associativity"]["drawing_references"]

workspace.command_manager.undo()
assert len(workspace.product_manager.product_reports) == before_reports
assert len(workspace.product_manager.parts) == before_parts
assert len(workspace.bim_manager.active_project.sheets) == before_drawings

workspace.command_manager.redo()
assert len(workspace.product_manager.product_reports) == before_reports + 1

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "ai_design_review.ksproj"
    ProjectSerializer().save(workspace, path)
    restored = ProjectSerializer().load(path)
    restored_report = restored.product_manager.product_reports[-1]
    assert restored_report.metadata.report_type == "AI Design Review"
    assert restored_report.metadata.properties["review_plan"]["summary"]["overall_quality_score"] == result.plan.scores.overall
    assert restored_report.metadata.properties["review_plan"]["recommendations"]
    assert restored_report.metadata.properties["review_plan"]["risks"]

diagnostics = ai.diagnostics()["design_review"]
assert diagnostics["successful"] == 1
assert diagnostics["failed"] == 3
assert diagnostics["rules_evaluated"] >= 42
assert diagnostics["recommendations_generated"] >= len(result.plan.recommendations)
assert diagnostics["risk_statistics"] >= len(result.plan.risks)
assert diagnostics["drawing_statistics"] >= 0
assert diagnostics["documentation_statistics"] >= 0

print("ai-design-review-ok")
