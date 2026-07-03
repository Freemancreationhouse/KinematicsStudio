from engine.geometry import Polygon2, Vector2

poly = Polygon2()

poly.add(Vector2(0, 0))
poly.add(Vector2(100, 0))
poly.add(Vector2(100, 50))
poly.add(Vector2(0, 50))

print(poly.count)
print(poly.center)
print(poly.bounding_box.width)
print(poly.bounding_box.height)