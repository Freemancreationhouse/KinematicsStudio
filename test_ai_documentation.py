import tempfile
from pathlib import Path

from engine.ai import AIDocumentationPlan, AIDocumentationResult, AIEngine, TextToCADValidationError
from engine.product import ProductionReport, ReadinessReport, ShopFloorDocument
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Documentation Workspace")
ai = AIEngine()
session = ai.create_session("Documentation Session", workspace)

try:
    ai.plan_engineering_documentation("Create manufacturing documentation", workspace, session)
    raise AssertionError("AI Documentation must reject missing parametric CAD models safely")
except TextToCADValidationError:
    pass

ai.execute_parametric_design(
    "Create a cnc machined flange diameter 100 mm height 12 mm hole diameter 40 mm with machinability",
    workspace,
    session,
)

try:
    ai.plan_engineering_documentation("Create manufacturing documentation", workspace, session)
    raise AssertionError("AI Documentation must reject missing associative drawings safely")
except TextToCADValidationError:
    pass

drawing = ai.execute_engineering_drawing(
    "Create an ANSI production drawing with detail view for cnc machining",
    workspace,
    session,
    "ANSI",
)
assert len(workspace.product_manager.product_reports) == 1
assert drawing.plan.associativity["drawing_references"]

plan = ai.plan_engineering_documentation(
    "Create ANSI manufacturing documentation with BOM assembly instructions inspection plan and revision history",
    workspace,
    session,
    "ANSI",
)
assert isinstance(plan, AIDocumentationPlan)
assert plan.validation.valid
assert plan.standard == "ANSI"
assert plan.document_type == "Manufacturing Documentation Package"
section_names = {section.name for section in plan.sections}
assert "Design Specification" in section_names
assert "Feature Summary" in section_names
assert "Parameter Summary" in section_names
assert "Manufacturing Process" in section_names
assert "Assembly Instructions" in section_names
assert "Inspection Plan" in section_names
assert "Revision History" in section_names
assert plan.bom_items
assert len({item.reference_id for item in plan.bom_items}) == len(plan.bom_items)
assert plan.revision_history[0].revision == "A"
assert plan.associativity["model_id"] == workspace.product_manager.parts[-1].id
assert plan.associativity["drawing_references"]
assert len(workspace.product_manager.product_reports) == 1

result = ai.execute_engineering_documentation(
    "Create ANSI manufacturing documentation with BOM assembly instructions inspection plan and revision history",
    workspace,
    session,
    "ANSI",
)
assert isinstance(result, AIDocumentationResult)
assert len(result.plan.bom_items) == len(plan.bom_items)
assert len(workspace.product_manager.product_reports) == 7
reports = workspace.product_manager.product_reports
assert any(report.metadata.report_type == "Engineering Documentation" for report in reports)
assert any(report.metadata.report_type == "Bill of Materials" for report in reports)
assert any(report.metadata.report_type == "Revision Documentation" for report in reports)
assert any(isinstance(report, ProductionReport) for report in reports)
assert any(isinstance(report, ShopFloorDocument) for report in reports)
assert any(isinstance(report, ReadinessReport) for report in reports)
for report in reports[1:]:
    assert report.target_id == result.plan.model_id
    assert report.metadata.properties["documentation_plan"]["associativity"]["model_id"] == result.plan.model_id
    assert result.plan.associativity["drawing_references"]

workspace.command_manager.undo()
assert len(workspace.product_manager.product_reports) == 1
assert workspace.product_manager.product_reports[0].metadata.report_type == "AI Drawing Studio"
assert len(workspace.product_manager.parts) == 1
assert len(workspace.bim_manager.active_project.sheets) == 1

workspace.command_manager.redo()
assert len(workspace.product_manager.product_reports) == 7

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "ai_documentation.ksproj"
    ProjectSerializer().save(workspace, path)
    restored = ProjectSerializer().load(path)
    restored_reports = restored.product_manager.product_reports
    assert len(restored_reports) == 7
    restored_bom = next(report for report in restored_reports if report.metadata.report_type == "Bill of Materials")
    assert restored_bom.metadata.properties["documentation_plan"]["bom_items"]
    assert restored_bom.metadata.properties["documentation_plan"]["revision_history"][0]["revision"] == "A"
    assert restored_bom.metadata.properties["documentation_plan"]["associativity"]["drawing_references"]

diagnostics = ai.diagnostics()["documentation"]
assert diagnostics["successful"] == 1
assert diagnostics["failed"] == 2
assert diagnostics["documents_generated"] == 6
assert diagnostics["bom_statistics"] >= 1
assert diagnostics["assembly_statistics"] >= 1
assert diagnostics["inspection_statistics"] >= 1
assert diagnostics["revision_statistics"] == 1
assert diagnostics["validation_statistics"] == 1

print("ai-documentation-ok")
