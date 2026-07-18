import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "collaboration3d.ksproj")
    app = CADApplication()
    session = app.workspace.collaboration_manager.create_session("Persist Session", owner="Owner")
    session.tags.append("review")
    annotation = app.workspace.annotation_manager3d.text_note("Persist Annotation", Vector3())
    review = app.workspace.review_manager.create("Persist Review", annotation)
    issue = app.workspace.issue_manager.create(
        "Persist Issue",
        Vector3(1.0, 2.0, 3.0),
        priority="High",
        assignee="Assignee",
    )
    issue.linked_annotation = annotation.id
    issue.linked_review_item = review.id
    issue.selected = True
    app.workspace.selection.select(issue)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_session = restored.workspace.collaboration_manager.active
    restored_issue = restored.workspace.issue_manager.issues[0]

    assert restored_session.name == "Persist Session"
    assert restored_session.metadata.owner == "Owner"
    assert restored_session.tags == ["review"]
    assert restored_issue.title == "Persist Issue"
    assert restored_issue.linked_annotation == restored.workspace.annotation_manager3d.annotations[0].id
    assert restored.workspace.selection.first is restored_issue

print("3d-collaboration-persistence-ok")
