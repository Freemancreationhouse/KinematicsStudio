from engine.commands import (
    AddCoordinationRuleCommand,
    AddReferenceInstanceCommand,
    AddReferenceModelCommand,
    ReloadReferenceCommand,
    RemoveReferenceModelCommand,
    UnloadReferenceCommand,
    UpdateReferenceInstanceCommand,
)
from engine.geometry import Vector3
from engine.references3d import CoordinationRule, ReferenceInstance, ReferenceModel, ReferenceTransform
from engine.workspace.workspace import Workspace


workspace = Workspace()
model = ReferenceModel("Coordination Model", "C:/refs/coordination.ifc")
workspace.command_manager.execute(AddReferenceModelCommand(workspace, model))
assert workspace.reference_manager.models == [model]

instance = ReferenceInstance(
    model.id,
    "Coordination Instance",
    ReferenceTransform(Vector3(5.0, 0.0, 0.0)),
)
workspace.command_manager.execute(AddReferenceInstanceCommand(workspace, instance))
assert workspace.reference_manager.instances == [instance]
assert workspace.selection.first is instance

workspace.command_manager.execute(
    UpdateReferenceInstanceCommand(
        instance,
        {"visible": True},
        {"visible": False},
    )
)
assert instance.visible is False
workspace.command_manager.undo()
assert instance.visible is True
workspace.command_manager.redo()
assert instance.visible is False

workspace.command_manager.execute(UnloadReferenceCommand(workspace, model))
assert model.status == "Unloaded"
workspace.command_manager.undo()
assert model.status == "Loaded"
workspace.command_manager.execute(ReloadReferenceCommand(workspace, model))
assert model.status == "Loaded"

rule = CoordinationRule("Shared Coordinates", "Coordinate Mapping")
workspace.command_manager.execute(AddCoordinationRuleCommand(workspace, rule))
assert workspace.coordination_manager.rules == [rule]
workspace.command_manager.undo()
assert workspace.coordination_manager.rules == []

workspace.command_manager.execute(RemoveReferenceModelCommand(workspace, model))
assert workspace.reference_manager.models == []
assert workspace.reference_manager.instances == []
workspace.command_manager.undo()
assert workspace.reference_manager.models == [model]
assert workspace.reference_manager.instances == [instance]

print("3d-reference-commands-ok")
