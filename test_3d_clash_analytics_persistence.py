import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.annotations3d import ReviewItem
from engine.cad.application import CADApplication
from engine.clashes import ClashResult
from engine.collaboration import Issue
from engine.commands import (
    AddClashResultCommand,
    AddIssueCommand,
    AddReviewItemCommand,
    LinkClashIssueCommand,
    LinkClashReviewCommand,
    SaveClashAnalyticsViewCommand,
    SaveClashDashboardLayoutCommand,
    UpdateClashKPIConfigurationCommand,
)
from engine.geometry import Vector3


qt_app = QApplication.instance() or QApplication([])

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "clash-analytics.ksproj")
    app = CADApplication()
    clash = ClashResult("Hard Clash", location=Vector3())
    issue = Issue("Persisted Issue", position=Vector3())
    review = ReviewItem("Persisted Review")
    app.workspace.command_manager.execute(AddClashResultCommand(app.workspace, clash))
    app.workspace.command_manager.execute(AddIssueCommand(app.workspace, issue))
    app.workspace.command_manager.execute(AddReviewItemCommand(app.workspace, review))
    app.workspace.command_manager.execute(LinkClashIssueCommand(app.workspace, clash, issue))
    app.workspace.command_manager.execute(LinkClashReviewCommand(app.workspace, clash, review))
    app.workspace.command_manager.execute(SaveClashAnalyticsViewCommand(
        app.workspace,
        "Persisted Analytics",
        {"trend_window": "All"},
    ))
    app.workspace.command_manager.execute(SaveClashDashboardLayoutCommand(
        app.workspace,
        "Persisted Layout",
        {"layout": "Analytics"},
    ))
    app.workspace.command_manager.execute(UpdateClashKPIConfigurationCommand(
        app.workspace,
        {"target_completion": 95.0},
    ))
    app.save_project(path)

    restored = CADApplication()
    restored.open_project(path)
    restored_clash = restored.workspace.clash_manager.results[0]

    assert restored_clash.linked_issue_id
    assert restored_clash.linked_review_id
    assert "Persisted Analytics" in restored.workspace.clash_manager.saved_analytics_views
    assert "Persisted Layout" in restored.workspace.clash_manager.dashboard_state["saved_layouts"]
    assert restored.workspace.clash_manager.kpi_configuration["target_completion"] == 95.0
    assert restored.workspace.clash_manager.analytics_summary(restored.workspace)["issue_summary"]["Open"] == 1

print("3d-clash-analytics-persistence-ok")
