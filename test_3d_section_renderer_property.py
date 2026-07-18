import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.render import Renderer3D
from engine.sections import SectionPlane
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
section = SectionPlane("Inspection Cut", Vector3(), Vector3(0.0, 0.0, 1.0), 250.0)
app.workspace.section_manager.add(section)
app.workspace.selection.select(section)
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(320, 240, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([section])

assert panel.type.text() == "SectionPlane"
assert panel.content.text() == "Inspection Cut"
assert panel.alignment.text() == "Enabled"

print("3d-section-renderer-property-ok")
