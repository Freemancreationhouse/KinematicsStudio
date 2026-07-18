import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.clashes import ClashResult
from engine.commands import AddClashResultCommand, UpdateClashReviewCommand
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "clash-review.ksproj")
    app = CADApplication()
    result = ClashResult("Hard Clash", location=Vector3(4.0, 5.0, 6.0))
    app.workspace.command_manager.execute(AddClashResultCommand(app.workspace, result))
    app.workspace.command_manager.execute(UpdateClashReviewCommand(
        app.workspace,
        result,
        {
            "status": result.status,
            "priority": result.priority,
            "assigned_reviewer": result.assigned_reviewer,
            "comments": result.comments,
            "resolution_notes": result.resolution_notes,
        },
        {
            "status": "Resolved",
            "priority": "Critical",
            "assigned_reviewer": "Review Lead",
            "comments": "Reviewed",
            "resolution_notes": "Accepted",
        },
    ))
    app.workspace.clash_manager.dock_state["search"] = "Hard"
    app.workspace.clash_manager.report_settings["group_by"] = "Status"
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_result = restored.workspace.clash_manager.results[0]

    assert restored_result.status == "Resolved"
    assert restored_result.priority == "Critical"
    assert restored_result.assigned_reviewer == "Review Lead"
    assert restored_result.comments == "Reviewed"
    assert restored.workspace.clash_manager.dock_state["search"] == "Hard"
    assert restored.workspace.clash_manager.report_settings["group_by"] == "Status"

print("3d-clash-review-persistence-ok")
