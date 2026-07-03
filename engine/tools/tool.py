from abc import ABC, abstractmethod


class Tool(ABC):

    def __init__(self):

        self.name = self.__class__.__name__

    # --------------------------------

    def activate(self):

        pass

    # --------------------------------

    def deactivate(self):

        pass

    # --------------------------------

    @abstractmethod
    def mouse_press(self, workspace, point):

        pass

    # --------------------------------

    @abstractmethod
    def mouse_move(self, workspace, point):

        pass

    # --------------------------------

    @abstractmethod
    def mouse_release(self, workspace, point):

        pass

    # --------------------------------

    def key_press(self, workspace, key):

        pass

    # --------------------------------

    def draw_preview(self, painter):

        pass