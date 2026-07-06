import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Object Properties")
changes = {"count": 0}


def changed():

    changes["count"] += 1


panel = PropertyPanel()
panel.set_workspace(workspace, changed)

walls = workspace.create_layer("Walls", "#AA0000", "Dashed", 0.35)
workspace.set_current_layer(walls)

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
workspace.add_entity(line)
workspace.selection.select(line)
panel.show_selection([line])

assert panel.type.text() == "LineEntity"
assert panel.layer.text() == "Walls"
assert panel.color.text() == "#AA0000"
assert panel.line_type.text() == "Dashed"
assert float(panel.line_weight.text()) == 0.35

panel.x.setText("5")
panel.x.editingFinished.emit()
assert line.start.x == 5
workspace.command_manager.undo()
assert line.start.x == 0
workspace.command_manager.redo()
assert line.start.x == 5

panel.length.setText("20")
panel.length.editingFinished.emit()
assert round(line.end.x - line.start.x, 2) == 20

panel.angle.setText("90")
panel.angle.editingFinished.emit()
assert round(line.end.x, 2) == round(line.start.x, 2)
assert round(line.end.y - line.start.y, 2) == 20

default_layer = workspace.layer_manager.get("0")
panel.layer.setCurrentText("0")
assert line.layer is default_layer
workspace.command_manager.undo()
assert line.layer is walls
workspace.command_manager.redo()
assert line.layer is default_layer

panel.visible.setChecked(False)
assert not line.visible
workspace.command_manager.undo()
assert line.visible

panel.locked.setChecked(True)
assert line.locked
workspace.command_manager.undo()
assert not line.locked

panel.layer.setCurrentText("Walls")
panel.color.setText("#00AAFF")
panel.color.editingFinished.emit()
assert walls.color == "#00AAFF"
assert line.display_color == "#00AAFF"
workspace.command_manager.undo()
assert walls.color == "#AA0000"
workspace.command_manager.redo()
assert walls.color == "#00AAFF"

rect = RectangleEntity(Vector2(0, 0), Vector2(10, 10))
workspace.add_entity(rect)
panel.show_selection([rect])
panel.width.setText("25")
panel.width.editingFinished.emit()
assert rect.width == 25
panel.height.setText("15")
panel.height.editingFinished.emit()
assert rect.height == 15

circle = CircleEntity(Vector2(5, 5), 10)
workspace.add_entity(circle)
panel.show_selection([circle])
panel.radius.setText("12")
panel.radius.editingFinished.emit()
assert circle.radius == 12
panel.diameter.setText("30")
panel.diameter.editingFinished.emit()
assert circle.radius == 15

panel.show_selection([line, rect])
assert panel.type.text() == "Multiple (2)"

print("object-properties-ok")
