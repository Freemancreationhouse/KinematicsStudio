class GestureState:

    IDLE = 0
    SKETCH = 1
    SELECT = 2
    PAN = 3

    def __init__(self):

        self.mode = self.IDLE

    def set(self, mode):

        self.mode = mode

    def is_sketch(self):

        return self.mode == self.SKETCH

    def is_select(self):

        return self.mode == self.SELECT

    def is_pan(self):

        return self.mode == self.PAN