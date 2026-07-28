import tempfile
from pathlib import Path

from engine.ai import AIAutomationPlan, AIAutomationResult, AIEngine, TextToCADValidationError
from engine.storage import ProjectSerializer
from engine.workspace.workspace import Workspace


workspace = Workspace("AI Automation Workspace")
ai = AIEngine()
session = ai.create_session("Automation Session", workspace)

try:
    ai.execute_automation_workflow(
        "Create documentation package for the selected engineering model",
        workspace,
        session,
        "Documentation Package",
        "ISO",
    )
    raise AssertionError("AI Automation Studio must reject workflows with missing prerequisites safely")
except TextToCADValidationError:
    pass

before_parts = len(workspace.product_manager.parts)
before_features = len(workspace.product_manager.features)
before_reports = len(workspace.product_manager.product_reports)

plan = ai.plan_automation_workflow(
    "Create a complete ISO engineering package for a CNC machined flange diameter 100 mm height 12 mm hole diameter 40 mm with machinability inspection documentation and design review",
    workspace,
    session,
    "Complete Engineering Package",
    "ISO",
)
assert isinstance(plan, AIAutomationPlan)
assert plan.template.name == "Complete Engineering Package"
assert [step.module for step in plan.steps] == ["parametric_design", "drawing", "documentation", "review"]
assert plan.validation.valid
assert plan.dependencies
assert plan.completion_criteria
assert plan.explanation["execution_order"] == ["Parametric Design", "Engineering Drawing", "Engineering Documentation", "Design Review"]
assert len(workspace.product_manager.parts) == before_parts
assert len(workspace.product_manager.features) == before_features
assert len(workspace.product_manager.product_reports) == before_reports

result = ai.execute_automation_workflow(
    "Create a complete ISO engineering package for a CNC machined flange diameter 100 mm height 12 mm hole diameter 40 mm with machinability inspection documentation and design review",
    workspace,
    session,
    "Complete Engineering Package",
    "ISO",
)
assert isinstance(result, AIAutomationResult)
assert all(record.status == "completed" for record in result.execution_records)
assert [record.module for record in result.execution_records] == ["parametric_design", "drawing", "documentation", "review"]
assert "parametric_design" in result.generated_outputs
assert "drawing" in result.generated_outputs
assert "documentation" in result.generated_outputs
assert "review" in result.generated_outputs
assert workspace.product_manager.parts
assert workspace.product_manager.features
assert workspace.bim_manager.active_project.sheets

report_types = [report.metadata.report_type for report in workspace.product_manager.product_reports]
assert "AI Drawing Studio" in report_types
assert "Engineering Documentation" in report_types
assert "AI Design Review" in report_types
assert "AI Automation Workflow" in report_types
assert "AI Automation Report" in report_types

automation_report = workspace.product_manager.product_reports[-1]
assert automation_report.metadata.report_type == "AI Automation Report"
assert automation_report.metadata.properties["workflow_plan"]["template"]["name"] == "Complete Engineering Package"
assert len(automation_report.metadata.properties["execution_history"]) == 4
assert automation_report.metadata.properties["generated_outputs"]["review"]
workflow_report = workspace.product_manager.product_reports[-2]
assert workflow_report.metadata.report_type == "AI Automation Workflow"
assert workflow_report.metadata.properties["workflow_definition"]["step_modules"]

reports_after_execute = len(workspace.product_manager.product_reports)
parts_after_execute = len(workspace.product_manager.parts)
sheets_after_execute = len(workspace.bim_manager.active_project.sheets)

workspace.command_manager.undo()
assert len(workspace.product_manager.product_reports) == reports_after_execute - 2
assert len(workspace.product_manager.parts) == parts_after_execute
assert len(workspace.bim_manager.active_project.sheets) == sheets_after_execute

workspace.command_manager.redo()
assert len(workspace.product_manager.product_reports) == reports_after_execute
assert workspace.product_manager.product_reports[-1].metadata.report_type == "AI Automation Report"

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "ai_automation.ksproj"
    ProjectSerializer().save(workspace, path)
    restored = ProjectSerializer().load(path)
    restored_types = [report.metadata.report_type for report in restored.product_manager.product_reports]
    assert "AI Automation Workflow" in restored_types
    assert "AI Automation Report" in restored_types
    restored_automation = restored.product_manager.product_reports[-1]
    assert restored_automation.metadata.properties["workflow_plan"]["template"]["name"] == "Complete Engineering Package"
    assert len(restored_automation.metadata.properties["execution_history"]) == 4

diagnostics = ai.diagnostics()["automation_studio"]
assert diagnostics["successful"] == 1
assert diagnostics["failed"] >= 1
assert diagnostics["template_count"] >= 6
assert diagnostics["validation_statistics"] >= 4
assert diagnostics["optimization_statistics"] >= 1
assert diagnostics["reports_generated"] == 2

print("ai-automation-studio-ok")
