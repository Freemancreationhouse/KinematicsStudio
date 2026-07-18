from engine.entities import HatchEntity, RectangleEntity
from engine.geometry import Vector2
from engine.tools import HatchTool
from engine.workspace import Workspace


workspace = Workspace("Hatch Tool")
boundary = RectangleEntity(Vector2(0, 0), Vector2(100, 50))
workspace.add_entity(boundary)
workspace.selection.select(boundary)
workspace.set_current_pattern("ANSI31")

tool = HatchTool()
tool.mouse_move(workspace, Vector2(10, 10))
assert isinstance(tool.preview, HatchEntity)
assert tool.preview.pattern_name == "ANSI31"

tool.mouse_press(workspace, Vector2(10, 10))
assert isinstance(workspace.entities[-1], HatchEntity)
assert workspace.entities[-1].boundary_entities[0] is boundary

count = len(workspace.entities)
workspace.command_manager.undo()
assert len(workspace.entities) == count - 1
workspace.command_manager.redo()
assert len(workspace.entities) == count

tool.mouse_move(workspace, Vector2(10, 10))
tool.key_press(workspace, "Escape")
assert tool.preview is None

print("hatch-tool-ok")
