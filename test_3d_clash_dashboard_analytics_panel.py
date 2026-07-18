import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.annotations3d import ReviewItem
from engine.clashes import ClashResult
from engine.collaboration import Issue
from engine.commands import AddClashResultCommand, AddIssueCommand, AddReviewItemCommand
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace
from ui_v2.clash_dashboard_panel import ClashDashboardPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
first = ClashResult("Hard Clash", location=Vector3())
first.name = "Panel A"
first.severity = "Critical"
second = ClashResult("Reference Clash", location=Vector3(1.0, 0.0, 0.0))
second.name = "Panel B"
second.discipline = "MEP"
workspace.command_manager.execute(AddClashResultCommand(workspace, first))
workspace.command_manager.execute(AddClashResultCommand(workspace, second))
issue = Issue("Linked Issue", position=Vector3())
review = ReviewItem("Linked Review")
workspace.command_manager.execute(AddIssueCommand(workspace, issue))
workspace.command_manager.execute(AddReviewItemCommand(workspace, review))
workspace.clash_manager.open_result(first)

changed = []
panel = ClashDashboardPanel(workspace, lambda: changed.append(True))

assert "Project Health Score" in panel.health_score.text()
assert "Completion" in panel.completion.text()
assert panel.analytics_tree.topLevelItemCount() >= 5

panel.link_current_issue(issue)
assert first.linked_issue_id == issue.id

panel.link_current_review(review)
assert first.linked_review_id == review.id

assert panel.navigate_issue() is issue
assert workspace.selection.first is issue
assert panel.navigate_review() is review

first.discipline = "MEP"
related = panel.navigate_related_clash()
assert related is second

panel.save_analytics_view("Panel Analytics")
panel.save_dashboard_layout("Panel Layout")
assert "Panel Analytics" in workspace.clash_manager.saved_analytics_views
assert "Panel Layout" in workspace.clash_manager.dashboard_state["saved_layouts"]
assert changed

print("3d-clash-dashboard-analytics-panel-ok")
