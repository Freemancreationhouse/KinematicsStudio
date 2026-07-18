from engine.commands import (
    AddManufacturingValidationCommand,
    AddProductAnalysisCommand,
    AddProductPartCommand,
    AddProductReportCommand,
    AddProductValidationCommand,
    CreateProductDocumentCommand,
)
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    AnalysisResult,
    ManufacturingReport,
    ManufacturingRule,
    ProductPart,
    ValidationReport,
    ValidationResult,
    ValidationRule,
    ValidationSession,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Command Validation Mesh")
workspace.add_3d_entity(mesh)

workspace.command_manager.execute(CreateProductDocumentCommand(workspace, "Command Validation Product"))
part = ProductPart("Command Validation Part", "Command Validation Mesh")
workspace.command_manager.execute(AddProductPartCommand(workspace, part))

session = ValidationSession("Command Session", [part.id])
workspace.command_manager.execute(AddProductValidationCommand(workspace, session))
rule = ValidationRule("Command Rule", rule_type="Missing Data")
workspace.command_manager.execute(AddProductValidationCommand(workspace, rule))
result = ValidationResult("Command Result", session.id, rule.id, part.id)
workspace.command_manager.execute(AddProductValidationCommand(workspace, result))
analysis = AnalysisResult("Command Analysis", part.id)
workspace.command_manager.execute(AddProductAnalysisCommand(workspace, analysis))
manufacturing_rule = ManufacturingRule("Command Manufacturing Rule", "Sharp Edge Detection")
workspace.command_manager.execute(AddManufacturingValidationCommand(workspace, manufacturing_rule))
manufacturing_report = ManufacturingReport("Command Manufacturing Report", part.id, [manufacturing_rule.id], [result.id])
workspace.command_manager.execute(AddManufacturingValidationCommand(workspace, manufacturing_report))
report = ValidationReport("Command Validation Report", part.id, [result.id])
workspace.command_manager.execute(AddProductReportCommand(workspace, report))

assert workspace.product_manager.validation_sessions == [session]
assert workspace.product_manager.validation_rules == [rule]
assert workspace.product_manager.validation_results == [result]
assert workspace.product_manager.analysis_results == [analysis]
assert workspace.product_manager.manufacturing_rules == [manufacturing_rule]
assert workspace.product_manager.manufacturing_reports == [manufacturing_report]
assert workspace.product_manager.product_reports == [report]

workspace.command_manager.undo()
assert workspace.product_manager.product_reports == []
workspace.command_manager.undo()
assert workspace.product_manager.manufacturing_reports == []
workspace.command_manager.undo()
assert workspace.product_manager.manufacturing_rules == []
workspace.command_manager.undo()
assert workspace.product_manager.analysis_results == []
workspace.command_manager.undo()
assert workspace.product_manager.validation_results == []

print("3d-product-validation-manufacturing-commands-ok")
