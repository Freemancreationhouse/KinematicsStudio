from .mouse_controller import MouseController
from .keyboard_controller import KeyboardController


class InputManager:

    def __init__(self):

        self.mouse = MouseController()
        self.keyboard = KeyboardController()

    # --------------------------------

    def reset(self):

        self.mouse.state.left = False
        self.mouse.state.middle = False
        self.mouse.state.right = False

        self.keyboard.state.ctrl = False
        self.keyboard.state.shift = False
        self.keyboard.state.alt = False

    # --------------------------------

    def mouse_press(self, button):
        """Handle a legacy mouse-button press through the shared mouse controller."""

        self.mouse.press(button)

    # --------------------------------

    def mouse_move(self, x, y):
        """Handle a legacy mouse move through the shared mouse controller."""

        self.mouse.move(x, y)

    # --------------------------------

    def mouse_release(self, button):
        """Handle a legacy mouse-button release through the shared mouse controller."""

        self.mouse.release(button)

    # --------------------------------

    @property
    def mouse_position(self):

        return self.mouse.state.mouse

    # --------------------------------

    @property
    def delta(self):

        return self.mouse.state.delta
