import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "annotations3d.ksproj")
    app = CADApplication()
    annotation = app.workspace.annotation_manager3d.pinned_note("Persist Note", Vector3(1.0, 2.0, 3.0))
    annotation.color = "#abcdef"
    review = app.workspace.review_manager.create("Persist Review", annotation, priority="High")
    review.add_comment("Saved", "Tester")
    app.workspace.selection.select(annotation)
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_annotation = restored.workspace.annotation_manager3d.annotations[0]
    restored_review = restored.workspace.review_manager.items[0]

    assert restored_annotation.text == "Persist Note"
    assert restored_annotation.display_color == "#FFFFFF"
    assert restored.workspace.selection.first is restored_annotation
    assert restored_review.title == "Persist Review"
    assert restored_review.annotation_ids == [restored_annotation.id]
    assert restored_review.comments[0]["text"] == "Saved"

print("3d-annotation-persistence-ok")
