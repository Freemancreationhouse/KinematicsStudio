import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from engine.bcf import BCFProject, BCFTopic
from engine.clashes import ClashResult
from engine.geometry import Vector3
from engine.workspace.workspace import Workspace
from ui_v2.bcf_topic_browser_panel import BCFTopicBrowserPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
project = BCFProject("Coordination")
topic = BCFTopic("Door Clash", "Door clearance issue", "Clash")
topic.priority = "High"
topic.assignee = "Coordinator"
project.add_topic(topic)
workspace.bcf_manager.add_project(project)

clash = ClashResult("Hard Clash", location=Vector3())
clash.name = "Door Clash Source"
workspace.clash_manager.add_result(clash)
topic.selection_ids = [clash.id]

changed = []
panel = BCFTopicBrowserPanel(workspace, lambda: changed.append(True))

assert panel.project_tree.topLevelItemCount() == 1
assert "BCF Topics: 1" in panel.summary.text()

parent = panel.topic_tree.topLevelItem(0)
item = parent.child(0)
panel.topic_tree.setCurrentItem(item)
assert panel.selected_topic() is topic

panel.change_status("In Review")
panel.change_priority("Critical")
panel.assign_topic("Lead")
panel.add_comment("Coordinate in BCF", "Reviewer")

assert topic.status == "In Review"
assert topic.priority == "Critical"
assert topic.assignee == "Lead"
assert topic.comments[-1].text == "Coordinate in BCF"

selected = panel.sync_selection()
assert selected == [clash]
assert clash.selected is True

panel.search.setText("Door")
panel.grouping.setCurrentText("Status")
assert workspace.bcf_manager.settings["browser_state"]["search"] == "Door"

workspace.command_manager.undo()
assert topic.comments == []

print("3d-bcf-topic-browser-panel-ok")
