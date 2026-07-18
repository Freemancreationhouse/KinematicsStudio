from engine.commands import (
    CreateBlockCommand,
    EditBlockCommand,
    InsertBlockCommand,
)
from engine.entities import BlockReference, CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.tools import InsertBlockTool
from engine.workspace import Workspace


workspace = Workspace("Block Workflow")

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
rect = RectangleEntity(Vector2(0, 0), Vector2(4, 4))
circle = CircleEntity(Vector2(2, 2), 2)
workspace.entities.extend([line, rect, circle])
workspace.selection.select(line)
workspace.selection.select(rect, True)
workspace.selection.select(circle, True)

create = CreateBlockCommand(
    workspace,
    "Mixed",
    Vector2(0, 0),
    workspace.selection.selected,
    replace=True,
)
workspace.command_manager.execute(create)

assert workspace.block_manager.count == 1
definition = workspace.block_manager.get("Mixed")
assert definition is not None
assert definition.id == 0
assert definition.count == 3
assert all(entity not in workspace.entities for entity in (line, rect, circle))
assert len(workspace.entities) == 1
assert isinstance(workspace.entities[0], BlockReference)
assert workspace.entities[0].definition is definition

workspace.command_manager.undo()
assert workspace.block_manager.count == 0
assert all(entity in workspace.entities for entity in (line, rect, circle))

workspace.command_manager.redo()
assert workspace.block_manager.count == 1
assert len(workspace.entities) == 1

insert = InsertBlockCommand(workspace, definition, Vector2(20, 20))
workspace.command_manager.execute(insert)
assert len([
    entity for entity in workspace.entities
    if isinstance(entity, BlockReference) and entity.definition is definition
]) == 2
workspace.command_manager.undo()
assert insert.reference not in workspace.entities
workspace.command_manager.redo()
assert insert.reference in workspace.entities

tool = InsertBlockTool()
workspace.block_manager.set_current(definition)
tool.mouse_move(workspace, Vector2(30, 30))
assert tool.preview is not None
tool.mouse_press(workspace, Vector2(30, 30))
assert any(
    isinstance(entity, BlockReference) and
    entity.insertion_point.x == 30 and
    entity.insertion_point.y == 30
    for entity in workspace.entities
)

edit_entities = workspace.begin_block_edit(definition)
assert len(edit_entities) == 3
edit_entities.append(LineEntity(Vector2(0, 0), Vector2(0, 10)))
assert workspace.save_block_edit()
assert definition.count == 4
assert all(
    reference.definition.count == 4
    for reference in workspace.entities
    if isinstance(reference, BlockReference)
)

workspace.command_manager.undo()
assert definition.count == 3
workspace.command_manager.redo()
assert definition.count == 4

nested = workspace.block_manager.create_definition(
    "Nested",
    Vector2(0, 0),
    [BlockReference(definition, Vector2(0, 0))]
)
assert nested.count == 1
assert isinstance(nested.entities[0], BlockReference)

manual_edit = EditBlockCommand(
    definition,
    [LineEntity(Vector2(1, 1), Vector2(2, 2))],
    workspace.block_manager,
)
manual_edit.execute()
assert definition.count == 1
manual_edit.undo()
assert definition.count == 4

print("block-workflow-ok")
