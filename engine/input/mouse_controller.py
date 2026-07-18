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

    # --------------------------------

    @property
    def x(self):
        """Return the current mouse X position for legacy callers."""

        return self.state.mouse.x

    # --------------------------------

    @property
    def y(self):
        """Return the current mouse Y position for legacy callers."""

        return self.state.mouse.y

    # --------------------------------

    @property
    def left(self):
        """Return whether the left mouse button is pressed."""

        return self.state.left

    # --------------------------------

    @property
    def dragging(self):
        """Return whether any mouse button is pressed while tracking movement."""

        return self.state.left or self.state.middle or self.state.right
