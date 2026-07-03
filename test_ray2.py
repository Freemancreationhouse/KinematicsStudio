from engine.geometry import Ray2, Vector2

ray = Ray2(Vector2(10, 20), Vector2(1, 1))

print(ray.point_at(10))