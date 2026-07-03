from engine.geometry import Transform2, Vector2

t = Transform2()

p = Vector2(10, 20)

print(

    t.translate(5, 10).apply(p)

)