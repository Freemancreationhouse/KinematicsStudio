from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Issue Workspace")
annotation = workspace.annotation_manager3d.text_note("Linked", Vector3())
review = workspace.review_manager.create("Review Link", annotation)
issue = workspace.issue_manager.create(
    "Clash A",
    Vector3(1.0, 2.0, 3.0),
    description="Pipe clash",
    priority="Critical",
    category="Coordination",
    reporter="QA",
    assignee="Modeler",
)
issue.linked_annotation = annotation.id
issue.linked_review_item = review.id
issue.attachments.append({"name": "snapshot.png", "kind": "placeholder"})
issue.tags.extend(["clash", "mep"])

assert issue.display_color == "#ef5350"
assert workspace.issue_manager.search("pipe") == [issue]
assert workspace.issue_manager.search("mep") == [issue]
assert workspace.issue_manager.filter(priority="Critical") == [issue]
assert workspace.issue_manager.linked_to_annotation(annotation) == [issue]
issue.resolve()
assert issue.status == "Resolved"
assert issue.resolved_date is not None
issue.reopen()
assert issue.status == "Open"

data = workspace.issue_manager.to_dict()
restored = Workspace("Restored Issue Workspace").issue_manager
restored.from_dict(data)
assert restored.issues[0].title == "Clash A"
assert restored.issues[0].attachments[0]["name"] == "snapshot.png"

print("3d-issue-manager-ok")
