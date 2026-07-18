import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from engine.entities import LeaderEntity, MTextEntity, TextEntity
from engine.geometry import Vector2
from engine.workspace import Workspace
from ui_v2.property_panel import PropertyPanel


app = QApplication.instance() or QApplication([])

workspace = Workspace("Annotation Properties")
changes = {"count": 0}


def changed():

    changes["count"] += 1


panel = PropertyPanel()
panel.set_workspace(workspace, changed)

text = TextEntity(Vector2(10, 20), "Old", 12, 0)
workspace.add_entity(text)
panel.show_selection([text])

assert panel.type.text() == "TextEntity"
panel.content.setText("New")
panel.content.editingFinished.emit()
assert text.text == "New"
workspace.command_manager.undo()
assert text.text == "Old"
workspace.command_manager.redo()
assert text.text == "New"

panel.height.setText("18")
panel.height.editingFinished.emit()
assert text.height == 18

mtext = MTextEntity(Vector2(0, 0), "Alpha", 100, 50, 10)
workspace.add_entity(mtext)
panel.show_selection([mtext])

panel.width.setText("150")
panel.width.editingFinished.emit()
assert mtext.box_width == 150
panel.alignment.setText("Center")
panel.alignment.editingFinished.emit()
assert mtext.alignment == "Center"
panel.content.setText("One\\nTwo")
panel.content.editingFinished.emit()
assert mtext.text == "One\nTwo"

leader = LeaderEntity(
    Vector2(0, 0),
    Vector2(20, 20),
    Vector2(70, 20),
    TextEntity(Vector2(76, 20), "Leader"),
)
workspace.add_entity(leader)
panel.show_selection([leader])

panel.content.setText("Callout")
panel.content.editingFinished.emit()
assert leader.text_entity.text == "Callout"
panel.x2.setText("90")
panel.x2.editingFinished.emit()
assert leader.landing_end.x == 90
assert leader.text_entity.position.x == 96

print("annotation-properties-ok")
