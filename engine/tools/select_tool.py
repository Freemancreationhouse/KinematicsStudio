from .tool import Tool


class SelectTool(Tool):

    def mouse_press(self, workspace, point):

        print("Select:", point)

    # --------------------------------

    def mouse_move(self, workspace, point):

        pass

    # --------------------------------

    def mouse_release(self, workspace, point):

        pass