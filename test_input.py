from engine.input import InputManager

i = InputManager()

i.mouse_press("left")

i.mouse_move(100, 200)

print(i.mouse.x, i.mouse.y)

print(i.mouse.dragging)

i.mouse_release("left")

print(i.mouse.left)