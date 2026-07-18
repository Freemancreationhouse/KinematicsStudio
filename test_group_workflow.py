from engine.commands import (
    AddEntityToGroupCommand,
    CreateGroupCommand,
    DeleteGroupCommand,
    RemoveEntityFromGroupCommand,
    RenameGroupCommand,
    UngroupCommand,
)
from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.groups import Group, GroupManager
from engine.tools import SelectTool
from engine.workspace import Workspace


workspace = Workspace("Group Workflow")

assert isinstance(workspace.group_manager, GroupManager)
assert workspace.groups is workspace.group_manager
assert workspace.group_manager.selection_enabled

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
rect = RectangleEntity(Vector2(20, 0), Vector2(30, 10))
circle = CircleEntity(Vector2(50, 0), 5)
workspace.entities.extend([line, rect, circle])

workspace.command_manager.execute(
    CreateGroupCommand(workspace, "Fixture", [line, rect])
)
group = workspace.group_manager.get("Fixture")
assert isinstance(group, Group)
assert group.id == 0
assert group.name == "Fixture"
assert group.count == 2
assert line in workspace.entities
assert rect in workspace.entities
assert group.contains(line)
assert group.contains(rect)

workspace.command_manager.undo()
assert workspace.group_manager.count == 0
assert line in workspace.entities
assert rect in workspace.entities
workspace.command_manager.redo()
group = workspace.group_manager.get("Fixture")
assert workspace.group_manager.count == 1

workspace.command_manager.execute(
    AddEntityToGroupCommand(workspace, group, circle)
)
assert group.count == 3
workspace.command_manager.undo()
assert group.count == 2
workspace.command_manager.redo()
assert group.count == 3

workspace.command_manager.execute(
    RemoveEntityFromGroupCommand(workspace, group, rect)
)
assert group.count == 2
assert not group.contains(rect)
workspace.command_manager.undo()
assert group.contains(rect)

workspace.command_manager.execute(
    RenameGroupCommand(workspace, group, "Fixture Renamed")
)
assert workspace.group_manager.get("Fixture Renamed") is group
workspace.command_manager.undo()
assert workspace.group_manager.get("Fixture") is group
workspace.command_manager.redo()
assert workspace.group_manager.get("Fixture Renamed") is group

tool = SelectTool()
tool.mouse_press(workspace, Vector2(5, 0))
tool.mouse_release(workspace, Vector2(5, 0))
assert set(workspace.selection.selected) == set(group.entities)

workspace.group_manager.selection_enabled = False
tool.mouse_press(workspace, Vector2(5, 0))
tool.mouse_release(workspace, Vector2(5, 0))
assert workspace.selection.selected == [line]
workspace.group_manager.selection_enabled = True

workspace.remove_entity(circle)
assert not group.contains(circle)

workspace.command_manager.execute(DeleteGroupCommand(workspace, group))
assert workspace.group_manager.count == 0
assert line in workspace.entities
assert rect in workspace.entities
workspace.command_manager.undo()
assert workspace.group_manager.get("Fixture Renamed") is group

workspace.command_manager.execute(UngroupCommand(workspace, group))
assert workspace.group_manager.count == 0
workspace.command_manager.undo()
assert workspace.group_manager.get("Fixture Renamed") is group

duplicate = workspace.group_manager.create("Fixture Renamed", [line])
assert duplicate.name == "Fixture Renamed 1"

print("group-workflow-ok")
