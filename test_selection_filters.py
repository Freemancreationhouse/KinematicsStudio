from engine.blocks.block_definition import BlockDefinition
from engine.entities import (
    AlignedDimensionEntity,
    ArcEntity,
    BlockReference,
    CircleEntity,
    HatchEntity,
    LeaderEntity,
    LineEntity,
    MTextEntity,
    PolylineEntity,
    RectangleEntity,
    SplineEntity,
    TextEntity,
)
from engine.geometry import Vector2
from engine.workspace import Workspace


workspace = Workspace("Selection Filters")
default_line = LineEntity(Vector2(0, 0), Vector2(10, 0))
polyline = PolylineEntity([Vector2(20, 0), Vector2(30, 0)])
spline = SplineEntity([Vector2(40, 0), Vector2(45, 10), Vector2(50, 0)])
rectangle = RectangleEntity(Vector2(60, 0), Vector2(70, 10))
circle = CircleEntity(Vector2(90, 5), 5)
arc = ArcEntity(Vector2(110, 5), 5, 0, 90)
definition = BlockDefinition("Door", origin=Vector2(0, 0), entities=[default_line.clone()])
block = BlockReference(definition, Vector2(130, 0))
text = TextEntity(Vector2(150, 0), "T")
mtext = MTextEntity(Vector2(170, 0), "A\nB")
leader = LeaderEntity(Vector2(190, 0), Vector2(200, 10), Vector2(220, 10))
dimension = AlignedDimensionEntity(Vector2(230, 0), Vector2(260, 0), Vector2(230, 10))
hatch = HatchEntity([
    Vector2(280, 0),
    Vector2(300, 0),
    Vector2(300, 20),
    Vector2(280, 20),
])

for entity in (
    default_line,
    polyline,
    spline,
    rectangle,
    circle,
    arc,
    block,
    text,
    mtext,
    leader,
    dimension,
    hatch,
):
    workspace.add_entity(entity)

hidden = workspace.create_layer("Hidden")
hidden.visible = False
locked = workspace.create_layer("Locked")
locked.locked = True
hidden_line = LineEntity(Vector2(0, 30), Vector2(10, 30))
locked_line = LineEntity(Vector2(20, 30), Vector2(30, 30))
workspace.assign_layer(hidden_line, hidden)
workspace.assign_layer(locked_line, locked)
workspace.entities.append(hidden_line)
workspace.entities.append(locked_line)
workspace.group_manager.create("Group A", [rectangle, circle])

selection_filter = workspace.selection.filter

expected_counts = {
    "All": 12,
    "Lines": 1,
    "Polylines": 1,
    "Splines": 1,
    "Rectangles": 1,
    "Circles": 1,
    "Arcs": 1,
    "Blocks": 1,
    "Groups": 2,
    "Text": 1,
    "MText": 1,
    "Leaders": 1,
    "Dimensions": 1,
    "Hatches": 1,
}

for type_name, expected in expected_counts.items():
    selection_filter.reset()
    selection_filter.type_filter = type_name
    assert len(workspace.selection.filtered_entities(workspace)) == expected

selection_filter.reset()
selection_filter.layer_names = {"Hidden"}
assert workspace.selection.filtered_entities(workspace) == []
assert workspace.selection.filtered_entities(workspace, include_unselectable=True) == [hidden_line]

selection_filter.reset()
selection_filter.lock_state = "Locked"
assert workspace.selection.filtered_entities(workspace) == []
assert workspace.selection.filtered_entities(workspace, include_unselectable=True) == [locked_line]

selection_filter.reset()
selection_filter.visibility = "Hidden"
assert workspace.selection.filtered_entities(workspace, include_unselectable=True) == [hidden_line]

selection_filter.reset()
print("selection-filters-ok")
