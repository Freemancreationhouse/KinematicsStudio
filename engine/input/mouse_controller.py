from .input_state import InputState


class MouseController:

    def __init__(self):

        self.state = InputState()

    # --------------------------------

    def press(self, button):

        if button == "left":
            self.state.left = True

        elif button == "middle":
            self.state.middle = True

        elif button == "right":
            self.state.right = True

    # --------------------------------

    def release(self, button):

        if button == "left":
            self.state.left = False

        elif button == "middle":
            self.state.middle = False

        elif button == "right":
            self.state.right = False

    # --------------------------------

    def move(self, x, y):

        self.state.update_mouse(x, y)