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
measurement = app.workspace.measurement_manager.point_to_point(
    Vector3(),
    Vector3(3.0, 4.0, 0.0),
)
app.workspace.measurement_manager.add(measurement)
app.workspace.selection.select(measurement)
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(320, 240, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 320, 240)
painter.end()

panel = PropertyPanel()
panel.set_workspace(app.workspace)
panel.show_selection([measurement])

assert panel.type.text() == "Measurement"
assert panel.content.text() == "Point-to-Point Distance"
assert "5" in panel.length.text()

print("3d-measurement-renderer-property-ok")
