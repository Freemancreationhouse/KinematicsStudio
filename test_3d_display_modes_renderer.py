import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.render import Renderer3D


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
mesh = MeshEntity(MeshData.box(20.0, 20.0, 20.0))
app.workspace.add_3d_entity(mesh)
app.camera3d.resize(320, 240)

renderer = Renderer3D()
renderer.camera = app.camera3d

for mode in (
    "wireframe",
    "hidden_line",
    "shaded",
    "shaded_with_edges",
    "x_ray",
    "bounding_box",
    "analysis_overlay",
):
    app.workspace.display_mode_manager.set_mode(mode)
    image = QImage(320, 240, QImage.Format_ARGB32)
    painter = QPainter(image)
    renderer.render(painter, app.workspace, 320, 240)
    painter.end()
    assert app.workspace.display_mode_manager.current_mode == mode

print("3d-display-modes-renderer-ok")
