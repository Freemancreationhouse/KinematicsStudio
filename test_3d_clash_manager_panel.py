import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.clashes import ClashResult
from engine.commands import AddClashResultCommand
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace
from ui_v2.clash_manager_panel import ClashManagerPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
first = ClashResult("Hard Clash", location=Vector3())
first.name = "A Clash"
first.severity = "High"
second = ClashResult("Reference Clash", location=Vector3(10.0, 0.0, 0.0))
second.name = "B Clash"
second.severity = "Low"
workspace.command_manager.execute(AddClashResultCommand(workspace, first))
workspace.command_manager.execute(AddClashResultCommand(workspace, second))

changed = []
panel = ClashManagerPanel(workspace, lambda: changed.append(True))

assert panel.tree.topLevelItemCount() >= 1
assert "Clashes:" in panel.summary.text()

panel.search.setText("A Clash")
assert "1 shown" in panel.summary.text()

panel.search.clear()
panel.severity_filter.setCurrentText("High")
assert "1 shown" in panel.summary.text()

panel.severity_filter.setCurrentText("All")
panel._select_tree_result(first)
panel.open_clash()
assert workspace.selection.first is first
assert workspace.clash_manager.current_result() is first

panel.status_editor.setCurrentText("Resolved")
panel.priority_editor.setCurrentText("Critical")
panel.reviewer_editor.setText("Reviewer A")
panel.comments.setPlainText("Clearance accepted")
panel.resolution_notes.setPlainText("No action")
panel.save_review()
assert first.status == "Resolved"
assert first.priority == "Critical"
assert first.assigned_reviewer == "Reviewer A"

workspace.command_manager.undo()
assert first.status == "Open"

with tempfile.TemporaryDirectory() as folder:
    pdf = panel.export_report("pdf", os.path.join(folder, "clashes.pdf"))
    csv = panel.export_report("csv", os.path.join(folder, "clashes.csv"))
    assert os.path.exists(pdf)
    assert os.path.getsize(pdf) > 0
    assert os.path.exists(csv)
    assert "A Clash" in open(csv, encoding="utf-8").read()

assert changed

print("3d-clash-manager-panel-ok")
