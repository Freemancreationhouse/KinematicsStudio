from engine.geometry.geometry_engine import GeometryEngine

v1 = GeometryEngine.Vector(10, 20, 0)
v2 = GeometryEngine.Vector(5, 10, 0)

print(v1 + v2)
print(v1 - v2)
print(v1.length())

p = GeometryEngine.Point(100, 50, 0)

print(GeometryEngine.Transform.translate(p, 20, 30))
print(GeometryEngine.Transform.scale(p, 2, 2))
print(GeometryEngine.Transform.rotate(p, 90))