import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.picking3d import PickingManager3D
from engine.render import Renderer3D


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
mesh_entity = MeshEntity(MeshData.box(100, 100, 100), display_mode="wireframe")
app.workspace.add_3d_entity(mesh_entity)
app.workspace.selection.select(mesh_entity)
app.camera3d.resize(640, 480)

screen = app.camera3d.project(mesh_entity.bounding_box3d.center)
assert screen is not None

hit = PickingManager3D().pick(
    app.workspace,
    app.camera3d.screen_ray(screen[0], screen[1]),
)
assert hit is not None
assert hit.entity is mesh_entity

renderer = Renderer3D()
renderer.camera = app.camera3d
renderer.debug_bounds = True

for mode in ("wireframe", "shaded"):
    mesh_entity.display_mode = mode
    image = QImage(640, 480, QImage.Format_ARGB32)
    painter = QPainter(image)
    renderer.render(painter, app.workspace, 640, 480)
    painter.end()

print("3d-mesh-renderer-ok")
