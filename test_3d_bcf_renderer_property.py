import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.bcf import BCFComment, BCFTopic, BCFViewpoint
from engine.geometry import Vector3
from engine.render.camera3d import Camera3D
from engine.render.renderer3d import Renderer3D
from engine.workspace.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace()
topic = BCFTopic("Rendered Topic", "Renderer and Property Panel")
topic.linked_issue_id = "issue-1"
topic.add_comment(BCFComment("Visible note"))
topic.add_viewpoint(BCFViewpoint(target=Vector3(0.0, 0.0, 0.0)))
workspace.bcf_manager.add_topic(topic)
workspace.selection.select(topic)

renderer = Renderer3D()
renderer.camera = Camera3D()
renderer.camera.resize(640, 480)

image = QImage(640, 480, QImage.Format_ARGB32)
image.fill(0)
painter = QPainter(image)
renderer.render(painter, workspace, 640, 480)
painter.end()

panel = PropertyPanel()
panel.show_selection([topic])

assert "BCFTopic" in panel.type.text()
assert panel.content.text() == "Rendered Topic"
assert "Issue: issue-1" in panel.line_type.text()
assert panel.length.text() == "Comments: 1"
assert panel.angle.text() == "Viewpoints: 1"

print("3d-bcf-renderer-property-ok")
