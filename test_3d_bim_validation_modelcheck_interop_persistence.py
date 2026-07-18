import os
import tempfile

from engine.bim import BIMInstance, ExchangeProfile, ExchangeRule, ModelCheckProfile, ModelCheckRule, ValidationProfile, ValidationRule
from engine.cad.application import CADApplication


app = CADApplication()
workspace = app.workspace
workspace.bim_manager.create_project("Persisted Batch K BIM")
instance = workspace.bim_manager.add_instance(BIMInstance("Persisted Validation Item"))

validation_rule = workspace.bim_manager.add_validation_item(
    ValidationRule("Persisted Classification", "Classification")
)
workspace.bim_manager.add_validation_item(
    ValidationProfile("Persisted Validation", [validation_rule.id])
)
workspace.bim_manager.validation_manager.run()

model_rule = workspace.bim_manager.add_model_check_item(
    ModelCheckRule("Persisted Material", "Missing Materials")
)
workspace.bim_manager.add_model_check_item(
    ModelCheckProfile("Persisted Model Check", [model_rule.id])
)
workspace.bim_manager.model_check_manager.run()

exchange_rule = workspace.bim_manager.add_interoperability_item(
    ExchangeRule("Persisted IFC", "IFC readiness")
)
workspace.bim_manager.add_interoperability_item(
    ExchangeProfile("Persisted Exchange", [exchange_rule.id])
)
workspace.bim_manager.interoperability_manager.statistics()
workspace.selection.select(instance)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "bim_batch_k.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    project = restored_workspace.bim_manager.active_project
    restored_instance = project.instances[0]

    assert project.validation_rules[0].name == "Persisted Classification"
    assert project.validation_results[0].target_id == restored_instance.id
    assert project.model_check_rules[0].name == "Persisted Material"
    assert project.model_check_results[0].target_id == restored_instance.id
    assert project.exchange_profiles[0].name == "Persisted Exchange"
    assert project.exchange_statistics.blocked_targets == 1
    assert restored_instance.selected is True

print("3d-bim-validation-modelcheck-interop-persistence-ok")
