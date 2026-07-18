from engine.collaboration import Issue, Session
from engine.commands import (
    AddIssueCommand,
    AddSessionCommand,
    ArchiveSessionCommand,
    DuplicateSessionCommand,
    RemoveIssueCommand,
    RestoreSessionCommand,
    UpdateIssueCommand,
    UpdateSessionCommand,
)
from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Collaboration Command Workspace")
session = Session("Command Session")
workspace.command_manager.execute(AddSessionCommand(workspace, session))
assert session in workspace.collaboration_manager.sessions

workspace.command_manager.execute(ArchiveSessionCommand(workspace, session))
assert session.status == "Archived"
workspace.command_manager.undo()
assert session.status == "Active"

workspace.command_manager.execute(RestoreSessionCommand(workspace, session))
assert session.status == "Active"
workspace.command_manager.execute(UpdateSessionCommand(session, {"notes": session.notes}, {"notes": "Updated"}))
assert session.notes == "Updated"
workspace.command_manager.undo()
assert session.notes == ""

workspace.command_manager.execute(DuplicateSessionCommand(workspace, session, "Command Copy"))
assert workspace.collaboration_manager.get("Command Copy") is not None

issue = Issue("Command Issue", position=Vector3())
workspace.command_manager.execute(AddIssueCommand(workspace, issue))
assert issue in workspace.issue_manager.issues
assert workspace.selection.first is issue

workspace.command_manager.execute(UpdateIssueCommand(issue, {"status": issue.status}, {"status": "In Progress"}))
assert issue.status == "In Progress"
workspace.command_manager.undo()
assert issue.status == "Open"

workspace.command_manager.execute(RemoveIssueCommand(workspace, issue))
assert issue not in workspace.issue_manager.issues
workspace.command_manager.undo()
assert issue in workspace.issue_manager.issues

print("3d-collaboration-command-ok")
