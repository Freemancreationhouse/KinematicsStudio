from engine.entities import CircleEntity, LineEntity, RectangleEntity
from engine.geometry import Vector2
from engine.workspace import Workspace


workspace = Workspace("Advanced Selection")
line_a = LineEntity(Vector2(0, 0), Vector2(100, 0))
line_b = LineEntity(Vector2(0, 0), Vector2(100, 0))
rectangle = RectangleEntity(Vector2(20, 20), Vector2(60, 60))
circle = CircleEntity(Vector2(120, 40), 15)

for entity in (line_a, line_b, rectangle, circle):
    workspace.add_entity(entity)

selection = workspace.selection

window = selection.select_window(workspace, Vector2(10, 10), Vector2(70, 70))
assert rectangle in window
assert circle not in window
assert selection.selected == [rectangle]

crossing = selection.select_window(
    workspace,
    Vector2(110, 30),
    Vector2(5, -10),
    crossing=True,
)
assert line_a in crossing
assert line_b in crossing

fence = selection.select_fence(workspace, [Vector2(40, -20), Vector2(40, 80)])
assert rectangle in fence
assert line_a in fence

lasso = selection.select_lasso(
    workspace,
    [
        Vector2(15, 15),
        Vector2(70, 15),
        Vector2(70, 70),
        Vector2(15, 70),
    ],
)
assert rectangle in lasso
assert circle not in lasso

first = selection.cycle_at_point(workspace, Vector2(50, 0))
second = selection.cycle_at_point(workspace, Vector2(50, 0))
assert first is not None
assert second is not None
assert first is not second

selection.select(line_a)
selection.select(rectangle)
previous = selection.recall_previous(workspace)
assert previous == [line_a]

selection.select(line_a)
inverted = selection.invert(workspace)
assert line_a not in inverted
assert rectangle in inverted
assert circle in inverted

selection.clear()
selection.select(line_a)
similar = selection.select_similar(workspace)
assert line_a in similar
assert line_b in similar
assert rectangle not in similar

print("advanced-selection-ok")
