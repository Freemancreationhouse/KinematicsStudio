from engine.geometry import Segment2, Vector2

s = Segment2(

    Vector2(0, 0),

    Vector2(3, 4)

)

print(s.length)
print(s.midpoint)
print(s.direction)