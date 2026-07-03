from engine.geometry import Matrix3, Vector2

v = Vector2(10, 0)

m = Matrix3().rotate(90)

print(m.transform(v))