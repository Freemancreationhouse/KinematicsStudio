from engine.commands import CreatePrimitiveCommand
from engine.geometry import Vector3
from engine.tools.tool import Tool


class Primitive3DTool(Tool):
    """Base interactive placement tool for generated 3D primitives."""

    primitive_type = "cube"
    default_parameters = {}

    def __init__(self):

        super().__init__()
        self.preview = None
        self.parameters = dict(self.default_parameters)
        self.display_mode = "wireframe"
        self._numeric_buffer = ""

    # --------------------------------

    def deactivate(self):
        """Clear transient preview and numeric input state."""

        self.preview = None
        self._numeric_buffer = ""

    # --------------------------------

    def set_dimensions(self, **parameters):
        """Set numeric primitive dimensions before placement."""

        self.parameters.update(parameters)
        self._numeric_buffer = ""

    # --------------------------------

    def mouse_press(self, workspace, point, additive=False):
        """Place the primitive at the picked point."""

        command = self._command(workspace, self._snap_point(workspace, point))
        workspace.command_manager.execute(command)
        self.preview = None

    # --------------------------------

    def mouse_move(self, workspace, point):
        """Update the live placement preview."""

        self.preview = self._command(
            workspace,
            self._snap_point(workspace, point),
        ).preview_entity()

    # --------------------------------

    def mouse_release(self, workspace, point, additive=False):
        """Primitive placement is click-confirmed."""

        pass

    # --------------------------------

    def key_press(self, workspace, key):
        """Handle Escape cancellation and simple numeric dimension entry."""

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            self._apply_numeric_buffer()
            return

        value = self._key_text(key)

        if value in "0123456789.-":
            self._numeric_buffer += value

    # --------------------------------

    def draw_preview(self, painter):
        """2D canvas preview hook retained for ToolManager compatibility."""

        pass

    # --------------------------------

    def _command(self, workspace, position):

        return CreatePrimitiveCommand(
            workspace,
            self.primitive_type,
            self.parameters,
            position=position,
            display_mode=self.display_mode,
            name=f"{self.primitive_type.title()} Primitive",
        )

    # --------------------------------

    def _apply_numeric_buffer(self):

        if not self._numeric_buffer:
            return

        try:
            value = float(self._numeric_buffer)
        except ValueError:
            self._numeric_buffer = ""
            return

        self.parameters[self.primary_dimension] = max(value, 0.0)
        self._numeric_buffer = ""

    # --------------------------------

    @property
    def primary_dimension(self):

        for key in ("size", "width", "radius", "major_radius"):
            if key in self.parameters:
                return key

        return "size"

    # --------------------------------

    def _point3(self, point):

        return Vector3(
            getattr(point, "x", 0.0),
            getattr(point, "y", 0.0),
            getattr(point, "z", 0.0),
        )

    # --------------------------------

    def _snap_point(self, workspace, point):

        world_point = self._point3(point)
        snap_manager = getattr(workspace, "snap_manager3d", None)

        if snap_manager is None:
            return world_point

        return snap_manager.snap_point(workspace, world_point)

    # --------------------------------

    def _key_text(self, key):

        if isinstance(key, str):
            return key

        return ""


class CubePrimitiveTool(Primitive3DTool):
    """Interactive cube primitive placement tool."""

    primitive_type = "cube"
    default_parameters = {"size": 100.0}


class BoxPrimitiveTool(Primitive3DTool):
    """Interactive box primitive placement tool."""

    primitive_type = "box"
    default_parameters = {"width": 100.0, "depth": 80.0, "height": 60.0}


class PlanePrimitiveTool(Primitive3DTool):
    """Interactive plane primitive placement tool."""

    primitive_type = "plane"
    default_parameters = {"width": 100.0, "depth": 100.0}


class CylinderPrimitiveTool(Primitive3DTool):
    """Interactive cylinder primitive placement tool."""

    primitive_type = "cylinder"
    default_parameters = {"radius": 50.0, "height": 100.0, "segments": 24}


class ConePrimitiveTool(Primitive3DTool):
    """Interactive cone primitive placement tool."""

    primitive_type = "cone"
    default_parameters = {"radius": 50.0, "height": 100.0, "segments": 24}


class SpherePrimitiveTool(Primitive3DTool):
    """Interactive sphere primitive placement tool."""

    primitive_type = "sphere"
    default_parameters = {"radius": 50.0, "segments": 24, "rings": 12}


class TorusPrimitiveTool(Primitive3DTool):
    """Interactive torus primitive placement tool."""

    primitive_type = "torus"
    default_parameters = {
        "major_radius": 60.0,
        "minor_radius": 15.0,
        "major_segments": 24,
        "minor_segments": 12,
    }


class PyramidPrimitiveTool(Primitive3DTool):
    """Interactive pyramid primitive placement tool."""

    primitive_type = "pyramid"
    default_parameters = {"width": 100.0, "depth": 100.0, "height": 100.0}


class PrismPrimitiveTool(Primitive3DTool):
    """Interactive prism primitive placement tool."""

    primitive_type = "prism"
    default_parameters = {"radius": 50.0, "height": 100.0, "sides": 6}


class CapsulePrimitiveTool(Primitive3DTool):
    """Interactive capsule primitive placement tool."""

    primitive_type = "capsule"
    default_parameters = {"radius": 30.0, "height": 120.0, "segments": 24, "rings": 12}
