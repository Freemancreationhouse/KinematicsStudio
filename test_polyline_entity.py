from engine.entities import PolylineEntity
from engine.geometry import Vector2

poly = PolylineEntity()

poly.add_point(Vector2(0, 0))
poly.add_point(Vector2(100, 0))
poly.add_point(Vector2(100, 50))

print(poly.count)
print(poly.bounding_box.width)
print(poly.bounding_box.height)

poly.move(10, 20)

print(poly.points[0])