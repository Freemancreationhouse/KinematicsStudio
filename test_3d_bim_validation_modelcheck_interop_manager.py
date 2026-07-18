from engine.bim import (
    BIMInstance,
    ExchangeProfile,
    ExchangeRule,
    ModelCheckProfile,
    ModelCheckRule,
    ValidationCategory,
    ValidationProfile,
    ValidationRule,
    ValidationSeverity,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.bim_manager.create_project("Validation Model Check BIM")
wall = workspace.bim_manager.add_instance(BIMInstance("Unclassified Wall"))

severity = workspace.bim_manager.add_validation_item(ValidationSeverity("Critical", 4))
category = workspace.bim_manager.add_validation_item(ValidationCategory("IFC Readiness"))
classification_rule = workspace.bim_manager.add_validation_item(
    ValidationRule("Classification Required", "Classification", category.id, severity.name)
)
ifc_rule = workspace.bim_manager.add_validation_item(
    ValidationRule("IFC Required", "IFC readiness", category.id, severity.name)
)
profile = workspace.bim_manager.add_validation_item(
    ValidationProfile("Core Validation", [classification_rule.id, ifc_rule.id])
)
validation_results = workspace.bim_manager.validation_manager.run(profile)

material_rule = workspace.bim_manager.add_model_check_item(
    ModelCheckRule("Material Required", "Missing Materials")
)
level_rule = workspace.bim_manager.add_model_check_item(
    ModelCheckRule("Level Required", "Missing Levels")
)
check_profile = workspace.bim_manager.add_model_check_item(
    ModelCheckProfile("Core Checks", [material_rule.id, level_rule.id])
)
check_results = workspace.bim_manager.model_check_manager.run(check_profile)

exchange_rule = workspace.bim_manager.add_interoperability_item(
    ExchangeRule("IFC Exchange", "IFC readiness")
)
workspace.bim_manager.add_interoperability_item(
    ExchangeProfile("Coordination Exchange", [exchange_rule.id])
)
exchange_status = workspace.bim_manager.interoperability_status_for(wall)
exchange_stats = workspace.bim_manager.interoperability_manager.statistics()

assert len(validation_results) == 2
assert workspace.bim_manager.validation_results_for(wall) == validation_results
assert workspace.bim_manager.active_project.validation_statistics.failures == 2
assert len(check_results) == 2
assert workspace.bim_manager.model_check_results_for(wall) == check_results
assert workspace.bim_manager.active_project.model_check_statistics.failures == 2
assert exchange_status["CAD"] is True
assert exchange_status["IFC"] is False
assert exchange_stats.blocked_targets == 1

print("3d-bim-validation-modelcheck-interop-manager-ok")
