from engine.input import InputState

inp = InputState()

inp.update_mouse(100, 200)

inp.update_mouse(120, 230)

print(inp.mouse)

print(inp.last_mouse)

print(inp.delta)