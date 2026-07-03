from .input_state import InputState


class KeyboardController:

    def __init__(self):

        self.state = InputState()

    # --------------------------------

    def key_press(self, key):

        if key.lower() == "ctrl":
            self.state.ctrl = True

        elif key.lower() == "shift":
            self.state.shift = True

        elif key.lower() == "alt":
            self.state.alt = True

    # --------------------------------

    def key_release(self, key):

        if key.lower() == "ctrl":
            self.state.ctrl = False

        elif key.lower() == "shift":
            self.state.shift = False

        elif key.lower() == "alt":
            self.state.alt = False