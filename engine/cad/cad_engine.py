from engine.workspace import WorkspaceManager
from engine.tools import ToolManager
from engine.render import (
    Camera,
    Camera3D,
    Renderer,
    Renderer3D,
    ViewTransform,
)
from engine.input import InputManager
from engine.snap import SnapManager


class CADEngine:
    """Coordinates workspace, tools, rendering, commands, input, and snapping."""

    def __init__(self):

        self.workspace_manager = WorkspaceManager()

        self.workspace = self.workspace_manager.create("Model")

        self.tool_manager = ToolManager()

        self.renderer = Renderer()

        self.camera = Camera()

        self.renderer.camera = self.camera

        self.renderer3d = Renderer3D()

        self.camera3d = Camera3D()

        self.renderer3d.camera = self.camera3d

        self.view = ViewTransform(self.camera)

        self.input = InputManager()
        self.snap_manager = SnapManager()

    # -----------------------------------------

    def update(self):

        pass

    # -----------------------------------------

    def set_workspace(self, workspace):
        """Replace the active workspace while preserving engine services."""

        self.workspace = workspace
        self.workspace_manager.workspaces[workspace.name] = workspace
        self.workspace_manager.active = workspace

        return workspace

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

    # -----------------------------------------

    def render3d(self, painter, width, height):
        """Render the 3D foundation scene."""

        self.renderer3d.render(
            painter,
            self.workspace,
            width,
            height,
        )
