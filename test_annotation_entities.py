from engine.commands import AddEntityCommand
from engine.entities import LeaderEntity, MTextEntity, TextEntity
from engine.geometry import Vector2
from engine.workspace import Workspace


workspace = Workspace("Annotation Entities")
notes = workspace.create_layer("Notes", "#FFCC00", "Continuous", 0.25)
workspace.set_current_layer(notes)

text = TextEntity(Vector2(10, 20), "Door", 12, 15)
workspace.command_manager.execute(AddEntityCommand(workspace.entities, text))

assert text.layer is notes
assert text.hit_test(Vector2(12, 22))
assert text.bounding_box.width > 0
assert text.bounding_box.height > 0

clone = text.clone()
clone.move(5, 5)
assert clone.position.x == 15
assert text.position.x == 10

mtext = MTextEntity(Vector2(0, 0), "one two three four", 36, 40, 10)
workspace.command_manager.execute(AddEntityCommand(workspace.entities, mtext))

assert len(mtext.lines()) > 1
assert mtext.hit_test(Vector2(5, 5))
assert mtext.layer is notes

leader = LeaderEntity(
    Vector2(0, 0),
    Vector2(20, 10),
    Vector2(60, 10),
    TextEntity(Vector2(66, 10), "Note"),
)
workspace.command_manager.execute(AddEntityCommand(workspace.entities, leader))

assert leader.hit_test(Vector2(10, 5))
assert leader.text_entity.text == "Note"
assert leader.layer is notes

assert len(workspace.entities) == 3
workspace.command_manager.undo()
assert len(workspace.entities) == 2
workspace.command_manager.redo()
assert len(workspace.entities) == 3

print("annotation-entities-ok")
