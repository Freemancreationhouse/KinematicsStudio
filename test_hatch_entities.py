from engine.commands import AddEntityCommand, UpdateEntityCommand
from engine.entities import HatchEntity, RectangleEntity
from engine.geometry import Vector2
from engine.geometry.hatch import is_closed_boundary
from engine.workspace import Workspace


workspace = Workspace("Hatch Entities")
hatch_layer = workspace.create_layer("Hatch", "#88CCFF", "Continuous", 0.25)
workspace.set_current_layer(hatch_layer)

boundary = RectangleEntity(Vector2(0, 0), Vector2(100, 50))
workspace.add_entity(boundary)

assert is_closed_boundary(boundary)

hatch = HatchEntity(boundary_entities=[boundary])
workspace.command_manager.execute(AddEntityCommand(workspace.entities, hatch))

assert hatch.layer is hatch_layer
assert hatch.pattern_name == "SOLID"
assert hatch.pattern is workspace.current_pattern
assert hatch.associative
assert hatch.hit_test(Vector2(10, 10))
assert hatch.bounding_box.width == 100

before = {"p1": boundary.p1.copy(), "p2": boundary.p2.copy()}
after = {"p1": boundary.p1.copy(), "p2": Vector2(120, 70)}
workspace.command_manager.execute(
    UpdateEntityCommand(boundary, workspace=workspace, before=before, after=after)
)

assert hatch.bounding_box.width == 120
assert hatch.bounding_box.height == 70
workspace.command_manager.undo()
assert hatch.bounding_box.width == 100
workspace.command_manager.redo()
assert hatch.bounding_box.width == 120

clone = hatch.clone()
assert clone.boundary_entities[0] is boundary
assert clone.hit_test(Vector2(20, 20))

print("hatch-entities-ok")
