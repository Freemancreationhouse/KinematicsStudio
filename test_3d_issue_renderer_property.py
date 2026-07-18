import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.render import Renderer3D
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
session = app.workspace.collaboration_manager.create_session("Panel Session", owner="Lead")
issue = app.workspace.issue_manager.create(
    "Panel Issue",
    Vector3(),
    priority="High",
    category="Review",
    assignee="Modeler",
)
app.workspace.selection.select(issue)
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(320, 240, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([issue])

assert panel.type.text() == "Issue"
assert panel.content.text() == "Panel Issue"
assert panel.line_type.text() == "Assignee: Modeler"
assert panel.line_weight.text() == "Priority: High"
assert panel.radius.text() == f"Session: {session.name}"

print("3d-issue-renderer-property-ok")
