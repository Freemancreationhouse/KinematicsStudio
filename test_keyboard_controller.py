from engine.input import KeyboardController

kb = KeyboardController()

kb.key_press("ctrl")
kb.key_press("shift")

print(kb.state.ctrl)
print(kb.state.shift)

kb.key_release("ctrl")

print(kb.state.ctrl)
print(kb.state.shift)