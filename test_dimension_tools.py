from engine.entities import (
    AlignedDimensionEntity,
    AngularDimensionEntity,
    DiameterDimensionEntity,
    LinearDimensionEntity,
    RadiusDimensionEntity,
)
from engine.geometry import Vector2
from engine.tools import (
    AlignedDimensionTool,
    AngularDimensionTool,
    DiameterDimensionTool,
    LinearDimensionTool,
    RadiusDimensionTool,
)
from engine.workspace import Workspace


workspace = Workspace("Dimension Tools")


def click(tool, *points):

    for point in points[:-1]:
        tool.mouse_press(workspace, point)

    tool.mouse_move(workspace, points[-1])
    assert tool.preview is not None
    tool.mouse_press(workspace, points[-1])


click(
    LinearDimensionTool(),
    Vector2(0, 0),
    Vector2(100, 0),
    Vector2(0, 25),
)
assert isinstance(workspace.entities[-1], LinearDimensionEntity)

click(
    AlignedDimensionTool(),
    Vector2(0, 0),
    Vector2(30, 40),
    Vector2(0, 20),
)
assert isinstance(workspace.entities[-1], AlignedDimensionEntity)

click(RadiusDimensionTool(), Vector2(0, 0), Vector2(50, 0))
assert isinstance(workspace.entities[-1], RadiusDimensionEntity)

click(DiameterDimensionTool(), Vector2(0, 0), Vector2(50, 0))
assert isinstance(workspace.entities[-1], DiameterDimensionEntity)

click(
    AngularDimensionTool(),
    Vector2(0, 0),
    Vector2(50, 0),
    Vector2(0, 50),
)
assert isinstance(workspace.entities[-1], AngularDimensionEntity)

count = len(workspace.entities)
workspace.command_manager.undo()
assert len(workspace.entities) == count - 1
workspace.command_manager.redo()
assert len(workspace.entities) == count

tool = LinearDimensionTool()
tool.mouse_press(workspace, Vector2(0, 0))
tool.key_press(workspace, "Escape")
assert tool.points == []

print("dimension-tools-ok")
