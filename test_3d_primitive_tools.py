from engine.geometry import Vector3
from engine.tools import (
    BoxPrimitiveTool,
    CapsulePrimitiveTool,
    ConePrimitiveTool,
    CubePrimitiveTool,
    CylinderPrimitiveTool,
    PlanePrimitiveTool,
    PrismPrimitiveTool,
    PyramidPrimitiveTool,
    SpherePrimitiveTool,
    ToolManager,
    TorusPrimitiveTool,
)
from engine.workspace import Workspace


tool_classes = [
    CubePrimitiveTool,
    BoxPrimitiveTool,
    PlanePrimitiveTool,
    CylinderPrimitiveTool,
    ConePrimitiveTool,
    SpherePrimitiveTool,
    TorusPrimitiveTool,
    PyramidPrimitiveTool,
    PrismPrimitiveTool,
    CapsulePrimitiveTool,
]

workspace = Workspace("Primitive Tool Workspace")
manager = ToolManager()

for tool_class in tool_classes:
    tool = tool_class()
    manager.register(tool)
    manager.activate(tool.name)
    tool.set_dimensions(**tool.parameters)
    tool.mouse_move(workspace, Vector3(1.0, 2.0, 3.0))
    assert tool.preview is not None
    assert tool.preview.primitive_type == tool.primitive_type
    tool.key_press(workspace, "Escape")
    assert tool.preview is None
    tool.key_press(workspace, "2")
    tool.key_press(workspace, "5")
    tool.key_press(workspace, "Enter")
    tool.mouse_press(workspace, Vector3(4.0, 5.0, 6.0))
    entity = workspace.scene3d.entities()[-1]
    assert entity.primitive_type == tool.primitive_type
    assert entity.selected

assert len(workspace.scene3d.entities()) == len(tool_classes)
assert "CubePrimitiveTool" in manager.tools
assert "CapsulePrimitiveTool" in manager.tools

print("3d-primitive-tools-ok")
