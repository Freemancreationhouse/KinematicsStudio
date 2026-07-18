import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.entities import HatchEntity, RectangleEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Hatch Properties")
panel = PropertyPanel()
panel.set_workspace(workspace)

boundary = RectangleEntity(Vector2(0, 0), Vector2(100, 50))
workspace.add_entity(boundary)
hatch = HatchEntity(boundary_entities=[boundary])
workspace.add_entity(hatch)

panel.show_selection([hatch])
assert panel.type.text() == "HatchEntity"
assert panel.content.text() == "SOLID"

panel.content.setText("ANSI31")
panel.content.editingFinished.emit()
assert hatch.pattern_name == "ANSI31"
workspace.command_manager.undo()
assert hatch.pattern_name == "SOLID"
workspace.command_manager.redo()
assert hatch.pattern_name == "ANSI31"

panel.length.setText("15")
panel.length.editingFinished.emit()
assert hatch.pattern_scale == 15

panel.angle.setText("30")
panel.angle.editingFinished.emit()
assert hatch.pattern_angle == 30

print("hatch-properties-ok")
