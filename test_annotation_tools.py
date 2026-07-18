from engine.entities import LeaderEntity, MTextEntity, TextEntity
from engine.geometry import Vector2
from engine.tools import LeaderTool, MTextTool, TextTool
from engine.workspace import Workspace


workspace = Workspace("Annotation Tools")

text_tool = TextTool()
text_tool.mouse_move(workspace, Vector2(5, 5))
assert isinstance(text_tool.preview, TextEntity)
text_tool.mouse_press(workspace, Vector2(5, 5))
assert isinstance(workspace.entities[-1], TextEntity)

mtext_tool = MTextTool()
mtext_tool.mouse_press(workspace, Vector2(0, 0))
mtext_tool.mouse_move(workspace, Vector2(100, 40))
assert isinstance(mtext_tool.preview, MTextEntity)
mtext_tool.mouse_press(workspace, Vector2(100, 40))
assert isinstance(workspace.entities[-1], MTextEntity)

leader_tool = LeaderTool()
leader_tool.mouse_press(workspace, Vector2(0, 0))
leader_tool.mouse_move(workspace, Vector2(80, 20))
assert isinstance(leader_tool.preview, LeaderEntity)
leader_tool.mouse_press(workspace, Vector2(80, 20))
assert isinstance(workspace.entities[-1], LeaderEntity)

count = len(workspace.entities)
workspace.command_manager.undo()
assert len(workspace.entities) == count - 1
workspace.command_manager.redo()
assert len(workspace.entities) == count

mtext_tool.mouse_press(workspace, Vector2(10, 10))
mtext_tool.key_press(workspace, "Escape")
assert mtext_tool.start is None

leader_tool.mouse_press(workspace, Vector2(10, 10))
leader_tool.key_press(workspace, "Escape")
assert leader_tool.arrow_point is None

print("annotation-tools-ok")
