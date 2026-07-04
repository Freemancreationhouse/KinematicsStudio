from engine.cad import CADEngine


class CADApplication:

    def __init__(self):

        self.engine = CADEngine()

    # --------------------------------

    def update(self):

        self.engine.update()

    # --------------------------------

    def render(self, painter, width, height, snap_result=None):

        self.engine.render(

            painter,

            width,

            height,

            snap_result

        )

    # --------------------------------

    @property
    def workspace(self):

        return self.engine.workspace

    # --------------------------------

    @property
    def tool_manager(self):

        return self.engine.tool_manager

    # --------------------------------

    @property
    def camera(self):

        return self.engine.camera

    # --------------------------------

    @property
    def snap_manager(self):

        return self.engine.snap_manager
