from engine.commands import UpdateCurveVerticesCommand, UpdatePolylineClosedCommand
from engine.entities import PolylineEntity, SplineEntity
from engine.geometry import Vector2


polyline = PolylineEntity(
    [Vector2(0, 0), Vector2(100, 0), Vector2(100, 50)]
)
assert polyline.count == 3
assert not polyline.closed
assert round(polyline.length, 2) == 150.0
assert polyline.hit_test(Vector2(50, 1))

polyline.add_vertex(Vector2(0, 50), 3)
polyline.closed = True
assert polyline.count == 4
assert round(polyline.length, 2) == 300.0
polyline.move_vertex(0, Vector2(10, 10))
assert polyline.points[0].x == 10
removed = polyline.remove_vertex(0)
assert removed.x == 10

clone = polyline.clone()
clone.move(10, 0)
assert polyline.points[0].x != clone.points[0].x

before = [point.copy() for point in polyline.points]
after = before + [Vector2(5, 5)]
command = UpdateCurveVerticesCommand(polyline, before, after)
command.execute()
assert polyline.count == len(after)
command.undo()
assert polyline.count == len(before)

closed_command = UpdatePolylineClosedCommand(polyline, False)
closed_command.execute()
assert not polyline.closed
closed_command.undo()
assert polyline.closed

spline = SplineEntity([
    Vector2(0, 0),
    Vector2(50, 100),
    Vector2(100, 0),
])
samples = spline.sampled_points()
assert len(samples) > len(spline.control_points)
assert spline.hit_test(Vector2(50, 100))
spline.move_control_point(1, Vector2(50, 80))
assert spline.control_points[1].y == 80
assert spline.length > 0

print("curve-entities-ok")
