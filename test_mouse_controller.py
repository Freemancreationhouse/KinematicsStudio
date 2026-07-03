from engine.input import MouseController

mouse = MouseController()

mouse.move(100, 200)

mouse.press("left")

print(mouse.state.mouse)
print(mouse.state.left)

mouse.release("left")

print(mouse.state.left)