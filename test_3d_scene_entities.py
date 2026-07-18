import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from engine.entities import (
    Line3D,
    PlaneEntity,
    Point3D,
    Polyline3D,
    ReferenceAxis,
    ReferenceGrid,
)
from engine.geometry import Vector3
from engine.picking3d import PickingManager3D
from engine.scene3d import SceneNode
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


qt_app = QApplication.instance() or QApplication([])

workspace = Workspace("3D Scene")
point = Point3D(Vector3(0, 0, 0))
line = Line3D(Vector3(-50, 0, 0), Vector3(50, 0, 0))
polyline = Polyline3D([
    Vector3(0, 0, 0),
    Vector3(0, 50, 0),
    Vector3(0, 50, 50),
])
plane = PlaneEntity(Vector3(0, 0, 0), 100, 80)
axis = ReferenceAxis(Vector3(0, 0, 0), Vector3(100, 0, 0), "X")
grid = ReferenceGrid(100, 25)

for entity in (point, line, polyline, plane, axis, grid):
    workspace.add_3d_entity(entity)

assert len(workspace.scene3d.entities()) == 6
assert point.layer_name == "0"
assert point.bounding_box3d.valid
assert line.bounding_sphere.radius > 0
assert len(polyline.segments()) == 2
assert len(plane.segments()) == 4
assert len(grid.segments()) > 0

parent = SceneNode("Parent")
child = SceneNode("Child", Point3D(Vector3(1, 2, 3)))
parent.add_child(child)
assert child.parent is parent
assert list(parent.walk())[1] is child
assert parent.update_bounds().valid

workspace.create_layer("Hidden3D")
workspace.assign_layer(point, workspace.layer_manager.get("Hidden3D"))
workspace.layer_manager.get("Hidden3D").visible = False
assert point not in workspace.visible_3d_entities()
workspace.layer_manager.get("Hidden3D").visible = True
assert point in workspace.visible_3d_entities()

workspace.layer_manager.get("Hidden3D").locked = True
assert point not in workspace.selectable_3d_entities()
workspace.layer_manager.get("Hidden3D").locked = False
assert point in workspace.selectable_3d_entities()

panel = PropertyPanel()
panel.set_workspace(workspace)
panel.show_selection([point])
assert panel.type.text() == "Point3D"
assert panel.layer.text() == "Hidden3D"
assert panel.content.text().startswith("Z:")

print("3d-scene-entities-ok")
