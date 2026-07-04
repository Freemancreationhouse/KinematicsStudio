from engine.workspace import WorkspaceManager
from engine.tools import ToolManager
from engine.render import Renderer, Camera, ViewTransform
from engine.input import InputManager
from engine.snap import SnapManager


class CADEngine:

    def __init__(self):

        self.workspace_manager = WorkspaceManager()

        self.workspace = self.workspace_manager.create("Model")

        self.tool_manager = ToolManager()

        self.renderer = Renderer()

        self.camera = Camera()

        self.renderer.camera = self.camera

        self.view = ViewTransform(self.camera)

        self.input = InputManager()
        self.snap_manager = SnapManager()

    # -----------------------------------------

    def update(self):

        pass

    # -----------------------------------------

    def render(

        self,

        painter,

        width,

        height,

        snap_result=None

    ):

        self.renderer.render(

            painter,

            self.workspace,

            self.tool_manager.current,

            width,

            height,

            snap_result

        )
