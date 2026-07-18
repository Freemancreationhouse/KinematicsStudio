from engine.annotations3d import ReviewItem
from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Review Workspace")
annotation = workspace.annotation_manager3d.text_note("Review me", Vector3())
review = workspace.review_manager.create(
    "Resolve clash",
    annotation,
    priority="High",
    author="Codex",
    category="Coordination",
)

assert review.annotation_ids == [annotation.id]
assert review.status == "Open"
assert review.priority == "High"
assert workspace.review_manager.linked_to(annotation) == [review]
review.add_comment("Needs follow-up", "Reviewer")
assert len(review.comments) == 1
review.set_resolved(True)
assert review.resolved is True
assert review.status == "Resolved"
assert workspace.review_manager.unresolved() == []

data = workspace.review_manager.to_dict()
restored = Workspace("Restored Review Workspace").review_manager
restored.from_dict(data)
assert restored.items[0].title == "Resolve clash"
assert restored.items[0].resolved is True

manual = ReviewItem("Manual")
manual.link_annotation(annotation.id)
assert annotation.id in manual.annotation_ids

print("3d-review-manager-ok")
