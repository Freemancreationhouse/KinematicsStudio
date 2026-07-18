import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.clashes import ClashResult
from engine.commands import AddClashResultCommand
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace
from ui_v2.clash_dashboard_panel import ClashDashboardPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
first = ClashResult("Hard Clash", location=Vector3())
first.name = "Dashboard A"
second = ClashResult("Reference Clash", location=Vector3(1.0, 0.0, 0.0))
second.name = "Dashboard B"
workspace.command_manager.execute(AddClashResultCommand(workspace, first))
workspace.command_manager.execute(AddClashResultCommand(workspace, second))
workspace.clash_manager.open_result(first)

changed = []
panel = ClashDashboardPanel(workspace, lambda: changed.append(True))

assert "Overall: 2 clashes" in panel.overall.text()
assert panel.summary_tree.topLevelItemCount() >= 5

panel.owner.setText("Coordinator")
panel.due_date.setText("2026-08-15")
panel.priority.setCurrentText("High")
panel.status.setCurrentText("In Review")
panel.resolution_category.setText("Adjust Pipe")
panel.approval_state.setCurrentText("Needs Work")
panel.discipline.setText("MEP")
panel.watch_list.setChecked(True)
panel.review_queue.setChecked(True)
panel.assign_clash()

assert first.owner == "Coordinator"
assert first.priority == "High"
assert first.review_queue is True

workspace.selection.select_many([first, second])
panel.owner.setText("Batch Owner")
panel.batch_assign()
assert second.owner == "Batch Owner"

panel.save_dashboard_filter("MEP Work")
assert "MEP Work" in workspace.clash_manager.dashboard_state["saved_filters"]

panel.template.setCurrentText("Discipline Report")
panel.scheduled.setChecked(True)
panel.schedule_interval.setCurrentText("Weekly")
panel.save_report_template()
assert workspace.clash_manager.report_settings["template"] == "Discipline Report"
assert workspace.clash_manager.report_settings["scheduled_enabled"] is True

with tempfile.TemporaryDirectory() as folder:
    pdf = panel.export_report("pdf", os.path.join(folder, "dashboard.pdf"))
    csv = panel.export_report("csv", os.path.join(folder, "dashboard.csv"))
    assert os.path.exists(pdf)
    assert os.path.getsize(pdf) > 0
    assert os.path.exists(csv)
    assert "Batch Owner" in open(csv, encoding="utf-8").read()

assert changed

print("3d-clash-dashboard-panel-ok")
