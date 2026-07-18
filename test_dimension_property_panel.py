import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.entities import LinearDimensionEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Dimension Properties")
panel = PropertyPanel()
panel.set_workspace(workspace)

custom = workspace.create_dimension_style("Custom", precision=1)
dimension = LinearDimensionEntity(Vector2(0, 0), Vector2(100, 0), Vector2(0, 25))
workspace.add_entity(dimension)
panel.show_selection([dimension])

assert panel.type.text() == "LinearDimensionEntity"
assert panel.dimension_style.text() == "Standard"

panel.content.setText("A")
panel.content.editingFinished.emit()
assert dimension.text_override == "A"
workspace.command_manager.undo()
assert dimension.text_override == ""
workspace.command_manager.redo()
assert dimension.text_override == "A"

panel.x.setText("10")
panel.x.editingFinished.emit()
assert dimension.point1.x == 10

panel.dimension_style.setText("Custom")
panel.dimension_style.editingFinished.emit()
assert dimension.dimension_style_name == "Custom"
assert dimension.dimension_style_id == custom.id

print("dimension-properties-ok")
