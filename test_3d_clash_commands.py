from engine.clashes import ClashResult, ClashSettings
from engine.commands import AddClashResultCommand, RemoveClashResultCommand, RunClashDetectionCommand, UpdateClashSettingsCommand
from engine.geometry import Vector3
from engine.references3d import ReferenceTransform
from engine.workspace.workspace import Workspace


workspace = Workspace()
model_a = workspace.reference_manager.create_model("A", "a.obj")
model_b = workspace.reference_manager.create_model("B", "b.obj")
workspace.reference_manager.create_instance(model_a, ReferenceTransform(Vector3()))
workspace.reference_manager.create_instance(model_b, ReferenceTransform(Vector3()))

workspace.command_manager.execute(RunClashDetectionCommand(workspace))
assert workspace.clash_manager.results
assert workspace.clash_manager.statistics.total == len(workspace.clash_manager.results)
workspace.command_manager.undo()
assert workspace.clash_manager.results == []
workspace.command_manager.redo()
assert workspace.clash_manager.results

before = workspace.clash_manager.settings
after = ClashSettings(clearance=25.0)
workspace.command_manager.execute(UpdateClashSettingsCommand(workspace, before, after))
assert workspace.clash_manager.settings.clearance == 25.0
workspace.command_manager.undo()
assert workspace.clash_manager.settings is before

manual = ClashResult("Rule Placeholder", location=Vector3(1.0, 2.0, 3.0))
workspace.command_manager.execute(AddClashResultCommand(workspace, manual))
assert manual in workspace.clash_manager.results
workspace.command_manager.execute(RemoveClashResultCommand(workspace, manual))
assert manual not in workspace.clash_manager.results
workspace.command_manager.undo()
assert manual in workspace.clash_manager.results

print("3d-clash-commands-ok")
