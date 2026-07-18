import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.clashes import ClashResult
from engine.commands import (
    AddClashResultCommand,
    SaveClashDashboardFilterCommand,
    UpdateClashAssignmentCommand,
    UpdateClashReportSettingsCommand,
    UpdateClashReportTemplateCommand,
)
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "clash-dashboard.ksproj")
    app = CADApplication()
    result = ClashResult("Hard Clash", location=Vector3())
    app.workspace.command_manager.execute(AddClashResultCommand(app.workspace, result))
    app.workspace.command_manager.execute(UpdateClashAssignmentCommand(
        app.workspace,
        [result],
        [{
            "owner": result.owner,
            "due_date": result.due_date,
            "priority": result.priority,
            "status": result.status,
            "resolution_category": result.resolution_category,
            "approval_state": result.approval_state,
            "discipline": result.discipline,
            "watch_list": result.watch_list,
            "review_queue": result.review_queue,
        }],
        {
            "owner": "Coordination Lead",
            "due_date": "2026-09-01",
            "priority": "Critical",
            "status": "In Review",
            "resolution_category": "Design Change",
            "approval_state": "Approved",
            "discipline": "Structure",
            "watch_list": True,
            "review_queue": False,
        },
    ))
    app.workspace.command_manager.execute(SaveClashDashboardFilterCommand(
        app.workspace,
        "Structure Critical",
        {"discipline": "Structure", "priority": "Critical"},
    ))
    app.workspace.command_manager.execute(UpdateClashReportTemplateCommand(
        app.workspace,
        "Executive Report",
        {"name": "Executive Report", "group_by": "Severity", "detail": "summary"},
    ))
    app.workspace.command_manager.execute(UpdateClashReportSettingsCommand(app.workspace, {
        "template": "Executive Report",
        "scheduled_enabled": True,
        "scheduled_interval": "Monthly",
    }))
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_result = restored.workspace.clash_manager.results[0]

    assert restored_result.owner == "Coordination Lead"
    assert restored_result.due_date == "2026-09-01"
    assert restored_result.approval_state == "Approved"
    assert restored_result.discipline == "Structure"
    assert restored_result.watch_list is True
    assert "Structure Critical" in restored.workspace.clash_manager.dashboard_state["saved_filters"]
    assert restored.workspace.clash_manager.report_settings["template"] == "Executive Report"
    assert restored.workspace.clash_manager.report_settings["scheduled_enabled"] is True

print("3d-clash-dashboard-persistence-ok")
