from engine.geometry import BoundingBox, Vector2

box = BoundingBox()

box.add(Vector2(10, 20))
box.add(Vector2(100, 50))
box.add(Vector2(30, 80))

print(box.width)
print(box.height)
print(box.center)