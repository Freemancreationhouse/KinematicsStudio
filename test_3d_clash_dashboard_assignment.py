from engine.clashes import ClashResult
from engine.commands import (
    AddClashResultCommand,
    SaveClashDashboardFilterCommand,
    UpdateClashAssignmentCommand,
    UpdateClashReportTemplateCommand,
)
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace


workspace = Workspace()
first = ClashResult("Hard Clash", location=Vector3())
first.name = "First"
first.severity = "High"
second = ClashResult("Reference Clash", location=Vector3(1.0, 0.0, 0.0))
second.name = "Second"
second.severity = "Low"

workspace.command_manager.execute(AddClashResultCommand(workspace, first))
workspace.command_manager.execute(AddClashResultCommand(workspace, second))

before = [
    {
        "owner": first.owner,
        "due_date": first.due_date,
        "priority": first.priority,
        "status": first.status,
        "resolution_category": first.resolution_category,
        "approval_state": first.approval_state,
        "discipline": first.discipline,
        "watch_list": first.watch_list,
        "review_queue": first.review_queue,
    },
    {
        "owner": second.owner,
        "due_date": second.due_date,
        "priority": second.priority,
        "status": second.status,
        "resolution_category": second.resolution_category,
        "approval_state": second.approval_state,
        "discipline": second.discipline,
        "watch_list": second.watch_list,
        "review_queue": second.review_queue,
    },
]
after = {
    "owner": "BIM Lead",
    "due_date": "2026-08-01",
    "priority": "Critical",
    "status": "In Review",
    "resolution_category": "Reroute",
    "approval_state": "Pending",
    "discipline": "MEP",
    "watch_list": True,
    "review_queue": True,
}
workspace.command_manager.execute(UpdateClashAssignmentCommand(workspace, [first, second], before, after))

assert first.owner == "BIM Lead"
assert second.owner == "BIM Lead"
assert first.watch_list is True
assert second.review_queue is True
assert workspace.clash_manager.dashboard_summary()["discipline"]["MEP"] == 2

workspace.command_manager.undo()
assert first.owner == ""
assert second.priority == "Normal"

workspace.command_manager.redo()
assert first.status == "In Review"

workspace.command_manager.execute(SaveClashDashboardFilterCommand(
    workspace,
    "MEP Open",
    {"status": "In Review", "discipline": "MEP"},
))
assert "MEP Open" in workspace.clash_manager.dashboard_state["saved_filters"]

workspace.command_manager.execute(UpdateClashReportTemplateCommand(
    workspace,
    "Discipline Report",
    {"name": "Discipline Report", "group_by": "Discipline", "detail": "detailed"},
))
assert workspace.clash_manager.report_template("Discipline Report")["group_by"] == "Discipline"

print("3d-clash-dashboard-assignment-ok")
