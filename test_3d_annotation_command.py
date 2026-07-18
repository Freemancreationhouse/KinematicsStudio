from engine.annotations3d import ReviewItem
from engine.commands import (
    AddAnnotation3DCommand,
    AddReviewItemCommand,
    RemoveAnnotation3DCommand,
    RemoveReviewItemCommand,
    UpdateAnnotation3DCommand,
    UpdateReviewItemCommand,
)
from engine.geometry import Vector3
from engine.workspace import Workspace


workspace = Workspace("3D Annotation Command Workspace")
annotation = workspace.annotation_manager3d.text_note("Command", Vector3())
workspace.annotation_manager3d.remove(annotation)

workspace.command_manager.execute(AddAnnotation3DCommand(workspace, annotation))
assert annotation in workspace.annotation_manager3d.annotations
assert workspace.selection.first is annotation

workspace.command_manager.undo()
assert annotation not in workspace.annotation_manager3d.annotations

workspace.command_manager.redo()
assert annotation in workspace.annotation_manager3d.annotations

workspace.command_manager.execute(
    UpdateAnnotation3DCommand(annotation, {"text": annotation.text}, {"text": "Updated"})
)
assert annotation.text == "Updated"
workspace.command_manager.undo()
assert annotation.text == "Command"

review = ReviewItem("Command Review")
workspace.command_manager.execute(AddReviewItemCommand(workspace, review))
assert review in workspace.review_manager.items
workspace.command_manager.execute(
    UpdateReviewItemCommand(review, {"priority": review.priority}, {"priority": "High"})
)
assert review.priority == "High"
workspace.command_manager.undo()
assert review.priority == "Normal"

workspace.command_manager.execute(RemoveReviewItemCommand(workspace, review))
assert review not in workspace.review_manager.items
workspace.command_manager.undo()
assert review in workspace.review_manager.items

workspace.command_manager.execute(RemoveAnnotation3DCommand(workspace, annotation))
assert annotation not in workspace.annotation_manager3d.annotations

print("3d-annotation-command-ok")
