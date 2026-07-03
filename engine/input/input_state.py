from engine.geometry import Vector2


class InputState:

    def __init__(self):

        self.mouse = Vector2()

        self.last_mouse = Vector2()

        self.left = False
        self.middle = False
        self.right = False

        self.ctrl = False
        self.shift = False
        self.alt = False

    # --------------------------------

    def update_mouse(self, x, y):

        self.last_mouse = self.mouse.copy()

        self.mouse.x = x
        self.mouse.y = y

    # --------------------------------

    @property
    def delta(self):

        return self.mouse - self.last_mouse