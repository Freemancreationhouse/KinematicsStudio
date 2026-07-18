import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication, QInputDialog

from engine.commands import AddEntityCommand
from engine.entities import BlockReference, CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.block_manager_panel import BlockManagerPanel
from ui_v2.main_window import MainWindow


app = QApplication.instance() or QApplication([])

workspace = Workspace("Block UI")
changed = {"count": 0}


def on_change():

    changed["count"] += 1


panel = BlockManagerPanel(workspace, on_change)
assert panel.table.rowCount() == 0

door = workspace.block_manager.create_definition(
    "Door",
    origin=Vector2(2, 3),
    entities=[
        LineEntity(Vector2(0, 0), Vector2(10, 0)),
        RectangleEntity(Vector2(0, 0), Vector2(4, 8)),
    ],
)
panel.refresh()

assert panel.table.rowCount() == 1
assert panel.table.item(0, 0).text() == "Door"
assert panel.table.item(0, 1).text() == str(door.id)
assert panel.table.item(0, 2).text() == "2"
assert panel.table.item(0, 3).text() == "No"
assert panel.table.item(0, 4).text() == "0"
assert panel.table.item(0, 5).text() == "2.00, 3.00"

reference = BlockReference(door, Vector2(20, 20))
workspace.command_manager.execute(AddEntityCommand(workspace.entities, reference))
panel.refresh()
assert panel.table.item(0, 4).text() == "1"

nested = workspace.block_manager.create_definition(
    "Nested Door",
    origin=Vector2(0, 0),
    entities=[reference.clone(), CircleEntity(Vector2(0, 0), 1)],
)
panel.refresh()

assert panel.table.rowCount() == 2
assert panel.table.item(1, 0).text() == "Nested Door"
assert panel.table.item(1, 2).text() == "2"
assert panel.table.item(1, 3).text() == "Yes"
assert panel.table.item(1, 4).text() == "0"

panel.new_block()
panel.delete_block()
panel.rename_block()
assert changed["count"] >= 1
assert workspace.block_manager.count == 2

nested_reference = BlockReference(nested, Vector2(0, 0))
workspace.command_manager.execute(
    AddEntityCommand(workspace.entities, nested_reference)
)
panel.refresh()
assert panel.table.item(1, 4).text() == "1"

source = LineEntity(Vector2(0, 0), Vector2(5, 0))
workspace.add_entity(source)
workspace.selection.select(source)
original_get_text = QInputDialog.getText
responses = [("Panel Block", True), ("0,0", True)]


def fake_get_text(*args, **kwargs):

    return responses.pop(0)


QInputDialog.getText = staticmethod(fake_get_text)
panel.new_block()
QInputDialog.getText = original_get_text
assert workspace.block_manager.get("Panel Block") is not None
assert any(isinstance(entity, BlockReference) for entity in workspace.entities)

panel.refresh()
panel.table.setCurrentCell(2, 0)
responses = [("Panel Block Renamed", True)]
QInputDialog.getText = staticmethod(fake_get_text)
panel.rename_block()
QInputDialog.getText = original_get_text
assert workspace.block_manager.get("Panel Block Renamed") is not None

window = MainWindow()
assert hasattr(window, "block_panel")
assert hasattr(window, "block_dock")
assert window.block_panel.table.rowCount() == 0
window.close()

print("block-manager-panel-ok")
