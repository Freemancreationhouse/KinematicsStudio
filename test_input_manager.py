from engine.input import InputManager

inp = InputManager()

inp.mouse.move(10, 20)
inp.mouse.move(25, 50)

print(inp.mouse_position)
print(inp.delta)

inp.keyboard.key_press("ctrl")

print(inp.keyboard.state.ctrl)

inp.reset()

print(inp.keyboard.state.ctrl)
print(inp.mouse.state.left)