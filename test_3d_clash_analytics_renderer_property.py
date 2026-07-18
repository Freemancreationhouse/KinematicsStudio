import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.clashes import ClashResult
from engine.commands import AddClashResultCommand
from engine.geometry import Vector3
from engine.render import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
clash = ClashResult("Hard Clash", location=Vector3())
clash.linked_issue_id = "issue-1"
clash.linked_review_id = "review-1"
clash.analytics_focus = True
workspace.command_manager.execute(AddClashResultCommand(workspace, clash))
workspace.clash_manager.open_result(clash)

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([clash])

assert "issue-1" in panel.alignment.text()
assert "review-1" in panel.alignment.text()

image = QImage(240, 180, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.render(painter, workspace, 240, 180)
painter.end()

print("3d-clash-analytics-renderer-property-ok")
