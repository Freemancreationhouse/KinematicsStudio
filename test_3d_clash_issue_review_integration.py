from engine.annotations3d import ReviewItem
from engine.clashes import ClashResult
from engine.collaboration import Issue
from engine.commands import (
    AddClashResultCommand,
    AddIssueCommand,
    AddReviewItemCommand,
    LinkClashIssueCommand,
    LinkClashReviewCommand,
    UpdateClashAssignmentCommand,
)
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace


workspace = Workspace()
clash = ClashResult("Hard Clash", location=Vector3())
workspace.command_manager.execute(AddClashResultCommand(workspace, clash))
issue = Issue("Issue A", position=Vector3())
review = ReviewItem("Review A")
workspace.command_manager.execute(AddIssueCommand(workspace, issue))
workspace.command_manager.execute(AddReviewItemCommand(workspace, review))
workspace.clash_manager.open_result(clash)

workspace.command_manager.execute(LinkClashIssueCommand(workspace, clash, issue))
assert clash.linked_issue_id == issue.id
assert issue.linked_entity == clash.id

workspace.command_manager.execute(UpdateClashAssignmentCommand(
    workspace,
    [clash],
    [{
        "owner": clash.owner,
        "due_date": clash.due_date,
        "priority": clash.priority,
        "status": clash.status,
        "resolution_category": clash.resolution_category,
        "approval_state": clash.approval_state,
        "discipline": clash.discipline,
        "watch_list": clash.watch_list,
        "review_queue": clash.review_queue,
    }],
    {
        "owner": "",
        "due_date": "",
        "priority": "Normal",
        "status": "Resolved",
        "resolution_category": "",
        "approval_state": "Approved",
        "discipline": "",
        "watch_list": False,
        "review_queue": False,
    },
))
workspace.command_manager.execute(LinkClashReviewCommand(workspace, clash, review))

assert clash.linked_review_id == review.id
assert review.status == "Resolved"
assert review.resolved is True
assert workspace.clash_manager.related_clashes(clash) == []

workspace.command_manager.undo()
assert clash.linked_review_id == ""
assert review.status == "Open"

workspace.command_manager.undo()
assert clash.status == "Open"

workspace.command_manager.undo()
assert clash.linked_issue_id == ""
assert issue.linked_entity is None

print("3d-clash-issue-review-integration-ok")
