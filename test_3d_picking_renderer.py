import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.entities import Point3D
from engine.geometry import Vector3
from engine.picking3d import PickingManager3D
from engine.render import Renderer3D


qt_app = QApplication.instance() or QApplication([])

app = CADApplication()
entity = Point3D(Vector3(0, 0, 0))
app.workspace.add_3d_entity(entity)
app.camera3d.resize(640, 480)
screen = app.camera3d.project(entity.position)
assert screen is not None

ray = app.camera3d.screen_ray(screen[0], screen[1])
picker = PickingManager3D()
hit = picker.pick(app.workspace, ray)
assert hit is not None
assert hit.entity is entity

app.workspace.selection.select(hit.entity)
assert entity.selected

hovered = picker.hover(app.workspace, ray)
assert hovered is entity
assert entity.hovered

renderer = Renderer3D()
renderer.camera = app.camera3d
renderer.debug_bounds = True
image = QImage(640, 480, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 640, 480)
painter.end()

print("3d-picking-renderer-ok")
