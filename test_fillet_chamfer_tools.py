from engine.entities import ArcEntity, LineEntity
from engine.geometry import Vector2
from engine.geometry.chamfer import chamfer_entities
from engine.geometry.fillet import fillet_entities
from engine.tools import ChamferTool, FilletTool
from engine.workspace.workspace import Workspace


def close(a, b, tolerance=1.0e-6):

    assert abs(a - b) <= tolerance


line_a = LineEntity(Vector2(0, 0), Vector2(20, 0))
line_b = LineEntity(Vector2(0, 0), Vector2(0, 20))

fillet = fillet_entities(line_a, line_b, 5, Vector2(10, 0), Vector2(0, 10))
assert fillet is not None
assert len(fillet) == 3
assert isinstance(fillet[2], ArcEntity)
close(fillet[2].radius, 5)
close(fillet[0].start.x, 5)
close(fillet[1].start.y, 5)

chamfer = chamfer_entities(line_a, line_b, 5, Vector2(10, 0), Vector2(0, 10))
assert chamfer is not None
assert len(chamfer) == 3
close(chamfer[2].start.x, 5)
close(chamfer[2].end.y, 5)

workspace = Workspace()
workspace.entities.extend([line_a, line_b])
tool = FilletTool()
tool.mouse_press(workspace, Vector2(10, 0))
tool.mouse_press(workspace, Vector2(0, 10))
tool.key_press(workspace, "1")
tool.key_press(workspace, "0")
assert tool.preview
tool.key_press(workspace, "Enter")
assert len(workspace.entities) == 3
assert any(isinstance(entity, ArcEntity) for entity in workspace.entities)
workspace.command_manager.undo()
assert len(workspace.entities) == 2
workspace.command_manager.redo()
assert len(workspace.entities) == 3

workspace = Workspace()
line_c = LineEntity(Vector2(0, 0), Vector2(20, 0))
line_d = LineEntity(Vector2(0, 0), Vector2(0, 20))
workspace.entities.extend([line_c, line_d])
tool = ChamferTool()
tool.mouse_press(workspace, Vector2(10, 0))
tool.mouse_press(workspace, Vector2(0, 10))
tool.key_press(workspace, "8")
assert tool.preview
tool.key_press(workspace, "Enter")
assert len(workspace.entities) == 3
workspace.command_manager.undo()
assert len(workspace.entities) == 2
workspace.command_manager.redo()
assert len(workspace.entities) == 3

tool.key_press(workspace, "Escape")
assert not tool.preview

print("fillet-chamfer-tools-ok")
