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
annotation = app.workspace.annotation_manager3d.text_note("Panel Note", Vector3())
review = app.workspace.review_manager.create("Panel Review", annotation, priority="High")
app.workspace.selection.select(annotation)
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(320, 240, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([annotation])

assert panel.type.text() == "Annotation3D"
assert panel.content.text() == "Panel Note"
assert panel.line_type.text() == f"Review: {review.status}"
assert panel.line_weight.text() == "Priority: High"

print("3d-annotation-renderer-property-ok")
