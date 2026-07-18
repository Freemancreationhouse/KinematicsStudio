import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.cad.application import CADApplication
from engine.geometry import (
    BoundingBox3D,
    BoundingSphere,
    Frustum,
    Matrix4,
    Plane,
    Quaternion,
    Ray3,
    Vector3,
)
from engine.render import Camera3D, CameraController3D, Renderer3D
from ui_v2.main_window import MainWindow


qt_app = QApplication.instance() or QApplication([])

v = Vector3(3, 4, 12)
assert round(v.length(), 5) == 13.0
assert Vector3(1, 0, 0).cross(Vector3(0, 1, 0)).z == 1.0

matrix = Matrix4.identity()
assert matrix.transform_point(Vector3(1, 2, 3)).to_tuple() == (1.0, 2.0, 3.0)

rotated = Quaternion.from_axis_angle(Vector3(0, 0, 1), 90).rotate_vector(Vector3(1, 0, 0))
assert abs(rotated.x) < 0.0001
assert abs(rotated.y - 1.0) < 0.0001

plane = Plane.from_point_normal(Vector3(0, 0, 5), Vector3(0, 0, 1))
assert plane.signed_distance(Vector3(0, 0, 7)) == 2.0

ray = Ray3(Vector3(1, 2, 3), Vector3(0, 0, 1))
assert ray.point_at(4).z == 7.0

box = BoundingBox3D()
box.add(Vector3(-1, -2, -3))
box.add(Vector3(4, 5, 6))
assert box.valid
assert box.center.to_tuple() == (1.5, 1.5, 1.5)

sphere = BoundingSphere.from_box(box)
assert sphere.radius > 0
assert Frustum().contains_sphere(sphere)

camera = Camera3D()
camera.resize(640, 480)
controller = CameraController3D(camera)
controller.orbit(10, -5)
controller.pan(4, 2)
controller.zoom(120)
assert camera.project(Vector3(0, 0, 0)) is not None
assert camera.view_matrix() is not None
assert camera.projection_matrix() is not None

app = CADApplication()
renderer = Renderer3D()
renderer.camera = app.camera3d
image = QImage(640, 480, QImage.Format_ARGB32)
painter = QPainter(image)
renderer.render(painter, app.workspace, 640, 480)
painter.end()

window = MainWindow()
window.show_3d_view()
assert window.view_stack.currentWidget() is window.viewport3d
window.show_2d_view()
assert window.view_stack.currentWidget() is window.canvas
window.close()

print("3d-foundation-ok")
