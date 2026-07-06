from engine.blocks import Block, BlockDefinition, BlockManager
from engine.commands import AddEntityCommand, CommandManager
from engine.entities import BlockReference, CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.workspace import Workspace


workspace = Workspace("Block Test")

assert isinstance(workspace.block_manager, BlockManager)
assert workspace.blocks is workspace.block_manager
assert workspace.block_manager.count == 0

source_line = LineEntity(Vector2(0, 0), Vector2(10, 0))
source_rect = RectangleEntity(Vector2(0, 0), Vector2(4, 3))
definition = workspace.block_manager.create_definition(
    "Door",
    origin=Vector2(1, 1),
    entities=[source_line, source_rect],
)

assert isinstance(definition, Block)
assert isinstance(definition, BlockDefinition)
assert definition.id == 0
assert definition.block_id == definition.id
assert definition.name == "Door"
assert definition.origin.x == 1
assert definition.origin.y == 1
assert definition.count == 2
assert workspace.block_manager.get("Door") is definition
assert workspace.block_manager.get_by_id(0) is definition
assert workspace.block_manager.names() == ["Door"]

duplicate = workspace.block_manager.create_definition("Door")
assert duplicate is definition
assert workspace.block_manager.count == 1

reference = BlockReference(
    definition,
    insertion_point=Vector2(100, 50),
    rotation=90,
    scale_x=2,
    scale_y=2,
)
assert reference.definition is definition
assert reference.definition_id == definition.id
assert reference.definition_name == "Door"

workspace.command_manager.execute(AddEntityCommand(workspace.entities, reference))
assert reference in workspace.entities
assert reference.layer_name == "0"
assert reference in workspace.visible_entities()
assert reference in workspace.selectable_entities()

box = reference.bounding_box
assert box.width > 0
assert box.height > 0

reference.move(10, -5)
assert reference.insertion_point.x == 110
assert reference.insertion_point.y == 45

clone = reference.clone()
assert clone is not reference
assert clone.definition is definition
assert clone.insertion_point.x == reference.insertion_point.x

nested_definition = workspace.block_manager.create_definition(
    "Nested Door",
    origin=Vector2(0, 0),
    entities=[reference.clone(), CircleEntity(Vector2(0, 0), 2)],
)
assert nested_definition.count == 2
assert isinstance(nested_definition.entities[0], BlockReference)

manager = CommandManager()
placed_nested = BlockReference(nested_definition, Vector2(0, 0))
manager.execute(AddEntityCommand(workspace.entities, placed_nested))
assert placed_nested in workspace.entities
manager.undo()
assert placed_nested not in workspace.entities
manager.redo()
assert placed_nested in workspace.entities

print("block-architecture-ok")
