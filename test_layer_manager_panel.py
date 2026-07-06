import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QInputDialog

from engine.entities import LineEntity
from engine.geometry import Vector2
from engine.tools import MoveTool, SelectTool, TrimTool
from engine.workspace import Workspace
from ui_v2.layer_manager_panel import LayerManagerPanel
from ui_v2.main_window import MainWindow
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Layer UI")
changed = {"count": 0}


def on_change():

    changed["count"] += 1


panel = LayerManagerPanel(workspace, on_change)
assert panel.table.rowCount() == 1
assert panel.table.item(0, 1).text() == "0"

workspace.create_layer("Walls", "#AA0000", "Dashed", 0.35)
panel.refresh()
assert panel.table.rowCount() == 2

panel.table.setCurrentCell(1, 1)
panel.set_current_layer()
assert workspace.current_layer.name == "Walls"

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
workspace.add_entity(line)
assert line.layer_name == "Walls"
assert line.display_color == "#AA0000"

color_item = panel.table.item(1, 4)
color_item.setText("#00AAFF")
assert workspace.layer_manager.get("Walls").color == "#00AAFF"
assert line.display_color == "#00AAFF"

panel.table.setCurrentCell(1, 5)
line_type_item = panel.table.item(1, 5)
line_type_item.setText("Center")
assert workspace.layer_manager.get("Walls").line_type == "Center"

panel.table.setCurrentCell(1, 6)
line_weight_item = panel.table.item(1, 6)
line_weight_item.setText("0.7")
assert workspace.layer_manager.get("Walls").line_weight == 0.7

property_panel = PropertyPanel()
property_panel.show_selection([line])
assert property_panel.layer.text() == "Walls"
assert property_panel.color.text() == "#00AAFF"

visible_item = panel.table.item(1, 2)
visible_item.setCheckState(Qt.Unchecked)
assert not workspace.layer_manager.get("Walls").visible
assert line not in workspace.visible_entities()
select = SelectTool()
select.mouse_press(workspace, Vector2(5, 0))
select.mouse_release(workspace, Vector2(5, 0))
assert not workspace.selection.selected

visible_item = panel.table.item(1, 2)
visible_item.setCheckState(Qt.Checked)
assert line in workspace.visible_entities()

lock_item = panel.table.item(1, 3)
lock_item.setCheckState(Qt.Checked)
assert workspace.layer_manager.get("Walls").locked
assert line not in workspace.selectable_entities()

tool = MoveTool()
tool.mouse_press(workspace, Vector2(5, 0))
tool.mouse_move(workspace, Vector2(15, 0))
tool.mouse_release(workspace, Vector2(15, 0))
assert line.start.x == 0
assert line.end.x == 10
trim = TrimTool()
trim.mouse_press(workspace, Vector2(5, 0))
assert trim.cutter is None

lock_item = panel.table.item(1, 3)
lock_item.setCheckState(Qt.Unchecked)
assert line in workspace.selectable_entities()

original_get_text = QInputDialog.getText
QInputDialog.getText = staticmethod(
    lambda *args, **kwargs: ("Renamed Walls", True)
)
panel.table.setCurrentCell(1, 1)
panel.rename_layer()
QInputDialog.getText = original_get_text
assert workspace.layer_manager.get("Renamed Walls") is not None
assert line.layer_name == "Renamed Walls"

panel.table.setCurrentCell(1, 1)
panel.delete_layer()
assert workspace.layer_manager.get("Renamed Walls") is None
assert line.layer_name == "0"

panel.table.setCurrentCell(0, 1)
assert not workspace.delete_layer("0")
assert not workspace.rename_layer("0", "Default")
assert workspace.layer_manager.get("0") is not None

window = MainWindow()
assert hasattr(window, "layer_panel")
assert window.layer_panel.table.rowCount() >= 1
window.close()

print("layer-manager-panel-ok")
