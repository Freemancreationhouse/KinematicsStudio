from engine.workspace import SelectionManager

from engine.entities import LineEntity

from engine.geometry import Vector2


s = SelectionManager()

line = LineEntity(

    Vector2(0, 0),

    Vector2(100, 0)

)

s.select(line)

print(s.count)

print(line.selected)

s.clear()

print(s.count)

print(line.selected)