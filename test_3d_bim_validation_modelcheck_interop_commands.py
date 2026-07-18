from engine.bim import BIMInstance, ExchangeProfile, ExchangeRule, ModelCheckProfile, ModelCheckRule, ValidationProfile, ValidationRule
from engine.commands import (
    AddBIMInteroperabilityCommand,
    AddBIMModelCheckCommand,
    AddBIMObjectCommand,
    AddBIMValidationCommand,
    CreateBIMProjectCommand,
    RefreshBIMInteroperabilityCommand,
    RunBIMModelCheckCommand,
    RunBIMValidationCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Batch K BIM"))
instance = BIMInstance("Command Validation Instance")
workspace.command_manager.execute(AddBIMObjectCommand(workspace, instance))

validation_rule = ValidationRule("Name Required", "Required Property", required_field="element_definition_id")
validation_profile = ValidationProfile("Command Validation Profile", [validation_rule.id])
workspace.command_manager.execute(AddBIMValidationCommand(workspace, validation_rule))
workspace.command_manager.execute(AddBIMValidationCommand(workspace, validation_profile))
workspace.command_manager.execute(RunBIMValidationCommand(workspace, validation_profile))

assert len(workspace.bim_manager.validation_results_for(instance)) == 1

workspace.command_manager.undo()
assert workspace.bim_manager.validation_results_for(instance) == []
workspace.command_manager.redo()
assert len(workspace.bim_manager.validation_results_for(instance)) == 1

model_rule = ModelCheckRule("Missing Material", "Missing Materials")
model_profile = ModelCheckProfile("Command Model Checks", [model_rule.id])
workspace.command_manager.execute(AddBIMModelCheckCommand(workspace, model_rule))
workspace.command_manager.execute(AddBIMModelCheckCommand(workspace, model_profile))
workspace.command_manager.execute(RunBIMModelCheckCommand(workspace, model_profile))

assert len(workspace.bim_manager.model_check_results_for(instance)) == 1

workspace.command_manager.undo()
assert workspace.bim_manager.model_check_results_for(instance) == []
workspace.command_manager.redo()
assert len(workspace.bim_manager.model_check_results_for(instance)) == 1

exchange_rule = ExchangeRule("IFC Readiness", "IFC readiness")
exchange_profile = ExchangeProfile("Command Exchange", [exchange_rule.id])
workspace.command_manager.execute(AddBIMInteroperabilityCommand(workspace, exchange_rule))
workspace.command_manager.execute(AddBIMInteroperabilityCommand(workspace, exchange_profile))
workspace.command_manager.execute(RefreshBIMInteroperabilityCommand(workspace))

assert workspace.bim_manager.active_project.exchange_statistics.blocked_targets == 1

workspace.command_manager.undo()
assert workspace.bim_manager.active_project.exchange_statistics.profiles == 1
workspace.command_manager.redo()
assert workspace.bim_manager.active_project.exchange_statistics.profiles == 1

print("3d-bim-validation-modelcheck-interop-commands-ok")
