import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QInputDialog

from engine.entities import LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.group_manager_panel import GroupManagerPanel
from ui_v2.main_window import MainWindow


app = QApplication.instance() or QApplication([])

workspace = Workspace("Group UI")
changed = {"count": 0}


def on_change():

    changed["count"] += 1


panel = GroupManagerPanel(workspace, on_change)
assert panel.table.rowCount() == 0

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
rect = RectangleEntity(Vector2(20, 0), Vector2(30, 10))
workspace.entities.extend([line, rect])
workspace.selection.select(line)
workspace.selection.select(rect, True)

original_get_text = QInputDialog.getText
responses = [("Panel Group", True)]


def fake_get_text(*args, **kwargs):

    return responses.pop(0)


QInputDialog.getText = staticmethod(fake_get_text)
panel.create_group()
QInputDialog.getText = original_get_text
assert workspace.group_manager.get("Panel Group") is not None
assert panel.table.rowCount() == 1
assert panel.table.item(0, 0).text() == "Panel Group"
assert panel.table.item(0, 1).text() == "0"
assert panel.table.item(0, 2).text() == "2"
assert changed["count"] >= 1

panel.table.setCurrentCell(0, 0)
responses = [("Renamed Group", True)]
QInputDialog.getText = staticmethod(fake_get_text)
panel.rename_group()
QInputDialog.getText = original_get_text
assert workspace.group_manager.get("Renamed Group") is not None
assert panel.table.item(0, 0).text() == "Renamed Group"

panel.ungroup()
assert workspace.group_manager.count == 0
workspace.command_manager.undo()
assert workspace.group_manager.get("Renamed Group") is not None

panel.refresh()
panel.table.setCurrentCell(0, 0)
panel.delete_group()
assert workspace.group_manager.count == 0
workspace.command_manager.undo()
assert workspace.group_manager.get("Renamed Group") is not None

window = MainWindow()
assert hasattr(window, "group_panel")
assert hasattr(window, "group_dock")
assert window.group_panel.table.rowCount() == 0
window.close()

print("group-manager-panel-ok")
