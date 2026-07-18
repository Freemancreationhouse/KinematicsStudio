import tempfile
from pathlib import Path

from engine.commands import MoveEntityCommand
from engine.entities import (
    AlignedDimensionEntity,
    BlockReference,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    MTextEntity,
    RectangleEntity,
    TextEntity,
)
from engine.geometry import Vector2
from engine.storage import ProjectSerializer
from engine.workspace import Workspace


serializer = ProjectSerializer()

workspace = Workspace("Persistence")
notes = workspace.create_layer("Notes", "#FFCC00", "Dashed", 0.35)
workspace.set_current_layer(notes)
workspace.pattern_manager.create("Custom", scale=12, angle=30)
workspace.set_current_pattern("Custom")
workspace.create_dimension_style("Small", text_height=8, arrow_size=3, precision=1)
workspace.set_current_dimension_style("Small")

line = LineEntity(Vector2(0, 0), Vector2(10, 0))
rect = RectangleEntity(Vector2(0, 0), Vector2(100, 50))
text = TextEntity(Vector2(5, 5), "Note", 10, 15)
mtext = MTextEntity(Vector2(10, 10), "Alpha Beta", 80, 40, 8)
leader = LeaderEntity(Vector2(0, 0), Vector2(20, 10), Vector2(60, 10))
dimension = AlignedDimensionEntity(Vector2(0, 0), Vector2(30, 40), Vector2(0, 20))

for entity in (line, rect, text, mtext, leader, dimension):
    workspace.add_entity(entity)

hatch = HatchEntity(boundary_entities=[rect])
workspace.add_entity(hatch)

definition = workspace.block_manager.create_definition(
    "Door",
    origin=Vector2(0, 0),
    entities=[line.clone(), text.clone()],
)
reference = BlockReference(definition, Vector2(200, 0))
workspace.add_entity(reference)
workspace.group_manager.create("Annotations", [text, mtext, leader])

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "project.ksproj"
    serializer.save(workspace, path)
    loaded = serializer.load(path)

assert loaded.name == "Persistence"
assert loaded.layer_manager.get("Notes").color == "#FFCC00"
assert loaded.current_layer.name == "Notes"
assert loaded.current_pattern.name == "Custom"
assert loaded.current_dimension_style.name == "Small"
assert loaded.block_manager.get("Door") is not None
assert loaded.group_manager.get("Annotations").count == 3
assert len(loaded.entities) == len(workspace.entities)

loaded_hatch = next(entity for entity in loaded.entities if isinstance(entity, HatchEntity))
loaded_rect = next(entity for entity in loaded.entities if isinstance(entity, RectangleEntity))
assert loaded_hatch.boundary_entities[0] is loaded_rect
assert loaded_hatch.pattern_name == "Custom"

loaded_line = next(entity for entity in loaded.entities if isinstance(entity, LineEntity))
command = MoveEntityCommand(loaded_line, 5, 0)
loaded.command_manager.execute(command)
assert loaded_line.start.x == 5
loaded.command_manager.undo()
assert loaded_line.start.x == 0

print("project-persistence-ok")
