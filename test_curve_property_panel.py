import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from engine.entities import PolylineEntity, SplineEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])
workspace = Workspace("Curve Properties")
panel = PropertyPanel()
panel.set_workspace(workspace)

polyline = PolylineEntity([
    Vector2(0, 0),
    Vector2(10, 0),
    Vector2(10, 10),
])
workspace.add_entity(polyline)
panel.show_selection([polyline])

assert panel.type.text() == "PolylineEntity"
assert panel.radius.text() == "3"
panel.alignment.setText("Closed")
panel.alignment.editingFinished.emit()
assert polyline.closed
workspace.command_manager.undo()
assert not polyline.closed

panel.show_selection([polyline])
panel.content.setText("0,0; 20,0; 20,20; 0,20")
panel.content.editingFinished.emit()
assert polyline.count == 4
workspace.command_manager.undo()
assert polyline.count == 3

spline = SplineEntity([
    Vector2(0, 0),
    Vector2(50, 100),
    Vector2(100, 0),
])
workspace.add_entity(spline)
panel.show_selection([spline])
assert panel.type.text() == "SplineEntity"
panel.x2.setText("120")
panel.x2.editingFinished.emit()
assert spline.control_points[-1].x == 120
workspace.command_manager.undo()
assert spline.control_points[-1].x == 100

print("curve-property-panel-ok")
