from engine.commands import (
    AddEntityCommand,
    EditBlockCommand,
    ExplodeBlockCommand,
)
from engine.entities import BlockReference, CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.tools import ExplodeBlockTool
from engine.workspace import Workspace


workspace = Workspace("Nested Blocks")
layer = workspace.create_layer("Blocks", "#AA5500", "Dashed", 0.5)
workspace.set_current_layer(layer)

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
workspace.add_entity(line)
assert line.layer_name == "Blocks"

base = workspace.block_manager.create_definition(
    "Base",
    Vector2(0, 0),
    [line],
)
assert base.entities[0].layer_name == "Blocks"

level_2 = workspace.block_manager.create_definition(
    "Level 2",
    Vector2(0, 0),
    [
        BlockReference(
            base,
            Vector2(20, 0),
            rotation=90,
            scale_x=2,
            scale_y=2,
        ),
        RectangleEntity(Vector2(0, 0), Vector2(4, 4)),
    ],
)
level_3 = workspace.block_manager.create_definition(
    "Level 3",
    Vector2(0, 0),
    [BlockReference(level_2, Vector2(5, 5)), CircleEntity(Vector2(0, 0), 2)],
)

assert level_2.count == 2
assert level_3.count == 2
assert not workspace.block_manager.has_circular_references()

try:
    EditBlockCommand(
        base,
        [BlockReference(level_3, Vector2(0, 0))],
        workspace.block_manager,
    ).execute()
    raise AssertionError("circular reference was not rejected")
except ValueError:
    pass

assert not workspace.block_manager.can_update(
    base,
    [BlockReference(level_3, Vector2(0, 0))]
)

base_ref = BlockReference(
    base,
    Vector2(100, 100),
    rotation=90,
    scale_x=2,
    scale_y=2,
)
workspace.command_manager.execute(AddEntityCommand(workspace.entities, base_ref))
explode = ExplodeBlockCommand(workspace, base_ref)
workspace.command_manager.execute(explode)

assert base_ref not in workspace.entities
assert len(explode.exploded) == 1
exploded_line = explode.exploded[0]
assert exploded_line.layer_name == "Blocks"
assert exploded_line.display_color == "#AA5500"
assert round(exploded_line.start.x, 2) == 100
assert round(exploded_line.start.y, 2) == 100
assert round(exploded_line.end.x, 2) == 100
assert round(exploded_line.end.y, 2) == 120

workspace.command_manager.undo()
assert base_ref in workspace.entities
assert exploded_line not in workspace.entities
workspace.command_manager.redo()
assert base_ref not in workspace.entities
assert exploded_line in workspace.entities

nested_ref = BlockReference(
    level_3,
    Vector2(50, 50),
    rotation=45,
    scale_x=1.5,
    scale_y=1.5,
)
workspace.command_manager.execute(AddEntityCommand(workspace.entities, nested_ref))
workspace.selection.clear()
workspace.selection.select(nested_ref)

tool = ExplodeBlockTool()
tool.mouse_press(workspace, Vector2(50, 50))
assert nested_ref not in workspace.entities
assert any(
    isinstance(entity, BlockReference) and entity.definition is level_2
    for entity in workspace.entities
)
assert any(
    isinstance(entity, CircleEntity)
    for entity in workspace.entities
)

nested_piece = next(
    entity for entity in workspace.entities
    if isinstance(entity, BlockReference) and entity.definition is level_2
)
assert round(nested_piece.insertion_point.x, 2) != 5
assert round(nested_piece.insertion_point.y, 2) != 5
assert round(nested_piece.rotation, 2) == 45
assert round(nested_piece.scale_x, 2) == 1.5

workspace.command_manager.undo()
assert nested_ref in workspace.entities
workspace.command_manager.redo()
assert nested_ref not in workspace.entities

print("block-nested-explode-ok")
