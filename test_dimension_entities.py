from engine.commands import AddEntityCommand
from engine.entities import (
    AlignedDimensionEntity,
    AngularDimensionEntity,
    DiameterDimensionEntity,
    LinearDimensionEntity,
    RadiusDimensionEntity,
)
from engine.geometry import Vector2
from engine.workspace import Workspace


workspace = Workspace("Dimension Entities")
dimensions = workspace.create_layer("Dimensions", "#00FFAA", "Continuous", 0.25)
workspace.set_current_layer(dimensions)
architectural = workspace.create_dimension_style(
    "Architectural",
    text_height=12,
    arrow_size=5,
    precision=1,
    units="mm",
)
workspace.set_current_dimension_style(architectural)

linear = LinearDimensionEntity(Vector2(0, 0), Vector2(100, 0), Vector2(0, 25))
aligned = AlignedDimensionEntity(Vector2(0, 0), Vector2(30, 40), Vector2(0, 20))
radius = RadiusDimensionEntity(Vector2(0, 0), Vector2(50, 0))
diameter = DiameterDimensionEntity(Vector2(0, 0), Vector2(50, 0))
angular = AngularDimensionEntity(Vector2(0, 0), Vector2(50, 0), Vector2(0, 50))

for entity in (linear, aligned, radius, diameter, angular):
    workspace.command_manager.execute(AddEntityCommand(workspace.entities, entity))
    assert entity.layer is dimensions
    assert entity.dimension_style is architectural
    assert entity.hit_test(entity.definition_points()[0])
    assert entity.bounding_box.width >= 0
    assert entity.bounding_box.height >= 0

assert linear.measurement() == 100
assert round(aligned.measurement(), 2) == 50
assert radius.formatted_measurement() == "R50.0"
assert diameter.formatted_measurement() == "Ø100.0"
assert angular.formatted_measurement() == "90.0°"

count = len(workspace.entities)
workspace.command_manager.undo()
assert len(workspace.entities) == count - 1
workspace.command_manager.redo()
assert len(workspace.entities) == count

clone = linear.clone()
clone.move(10, 10)
assert clone.point1.x == 10
assert linear.point1.x == 0

print("dimension-entities-ok")
