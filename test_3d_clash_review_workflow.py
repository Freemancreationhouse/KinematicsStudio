from engine.clashes import ClashResult
from engine.commands import AddClashResultCommand, UpdateClashReviewCommand
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace


workspace = Workspace()
result = ClashResult("Hard Clash", location=Vector3(1.0, 2.0, 3.0))
workspace.command_manager.execute(AddClashResultCommand(workspace, result))

before = {
    "status": result.status,
    "priority": result.priority,
    "assigned_reviewer": result.assigned_reviewer,
    "comments": result.comments,
    "resolution_notes": result.resolution_notes,
}
after = {
    "status": "In Review",
    "priority": "High",
    "assigned_reviewer": "Coordinator",
    "comments": "Needs review",
    "resolution_notes": "Route change pending",
}
workspace.command_manager.execute(UpdateClashReviewCommand(workspace, result, before, after))

assert result.status == "In Review"
assert result.priority == "High"
assert result.assigned_reviewer == "Coordinator"
assert result.comments == "Needs review"
assert result.history
assert workspace.clash_manager.statistics.unresolved == 1

workspace.command_manager.undo()
assert result.status == "Open"
assert result.priority == "Normal"

workspace.command_manager.redo()
assert result.status == "In Review"

workspace.clash_manager.open_result(result)
assert workspace.clash_manager.current_result() is result
assert workspace.clash_manager.next_result() is result
assert workspace.clash_manager.previous_result() is result

print("3d-clash-review-workflow-ok")
