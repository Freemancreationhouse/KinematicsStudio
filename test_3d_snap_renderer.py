import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData, Vector3
from engine.render import Renderer3D
from engine.snap import SnapResult3D


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
entity = MeshEntity(MeshData.box(100, 100, 100))
app.workspace.add_3d_entity(entity)
app.workspace.snap_manager3d.active_snap = SnapResult3D(
    Vector3(),
    "ORIGIN",
    entity,
)
app.workspace.snap_manager3d.highlighted_entity = entity
app.camera3d.resize(640, 480)

renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(640, 480, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 640, 480)
painter.end()

print("3d-snap-renderer-ok")
