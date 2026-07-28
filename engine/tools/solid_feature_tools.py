from engine.commands import CreateSolidFeatureCommand
from engine.entities import MeshEntity
from engine.geometry import Vector3
from engine.geometry.solid_modeling import extrude_profile, loft_profiles, revolve_profile, sweep_profile
from engine.product import FeatureOptions
from engine.tools.tool import Tool


class SolidFeatureTool(Tool):
    """Base interactive tool for command-routed solid feature creation."""

    feature_type = "Extrude"
    default_options = {}
    default_parameters = {}
    primary_value = "distance"

    def __init__(self):
        super().__init__()
        self.preview = None
        self.options = dict(self.default_options)
        self.parameters = dict(self.default_parameters)
        self._anchor = None
        self._numeric_buffer = ""

    def deactivate(self):
        """Clear transient preview and numeric state."""

        self.preview = None
        self._anchor = None
        self._numeric_buffer = ""

    def set_options(self, **options):
        """Update feature options before creation."""

        self.options.update(options)

    def set_parameters(self, **parameters):
        """Update feature parameters before creation."""

        self.parameters.update(parameters)

    def mouse_press(self, workspace, point, additive=False):
        """Start dynamic placement or confirm the current feature."""

        picked = self._point3(point)
        if self._anchor is None:
            self._anchor = picked
            self.preview = self._preview_entity(picked)
            return

        self._commit(workspace, picked)

    def mouse_move(self, workspace, point):
        """Update live solid feature preview."""

        picked = self._point3(point)
        if self._anchor is None:
            self.preview = self._preview_entity(picked)
        else:
            self.preview = self._preview_entity(picked)

    def mouse_release(self, workspace, point, additive=False):
        """Solid feature placement is click-confirmed."""

    def key_press(self, workspace, key):
        """Handle numeric entry, Enter confirmation and Escape cancellation."""

        if key in ("Escape", "Esc", 0x01000000):
            self.deactivate()
            return

        if key in ("Enter", "Return", 0x01000004, 0x01000005):
            self._apply_numeric_buffer()
            self._commit(workspace, self._anchor or Vector3())
            return

        text = self._key_text(key)
        if text in "0123456789.-":
            self._numeric_buffer += text

    def draw_preview(self, painter):
        """2D canvas preview hook retained for ToolManager compatibility."""

    def _commit(self, workspace, point):
        options = self._feature_options(point)
        command = CreateSolidFeatureCommand(
            workspace,
            self.feature_type,
            options=options,
            parameters=self._feature_parameters(point),
            name=f"{self.feature_type} Feature",
        )
        workspace.command_manager.execute(command)
        self.deactivate()

    def _preview_entity(self, point):
        mesh = self._preview_mesh(point)
        entity = MeshEntity(
            mesh,
            name=f"{self.feature_type} Preview",
            display_mode="wireframe",
            primitive_type=self.feature_type.lower(),
            parameters=self._feature_options(point).to_dict() | self._feature_parameters(point),
        )
        entity.set_transform_state(position=Vector3())
        return entity

    def _preview_mesh(self, point):
        return extrude_profile(distance=self._distance(point))

    def _feature_options(self, point):
        options = FeatureOptions()
        for key, value in self.options.items():
            if hasattr(options, key):
                setattr(options, key, value)
        setattr(options, self.primary_value, self._primary_numeric(point))
        return options

    def _feature_parameters(self, point):
        return dict(self.parameters)

    def _primary_numeric(self, point):
        return self._distance(point)

    def _distance(self, point):
        if self._anchor is None:
            return float(self.options.get("distance", 100.0))
        return max(abs((point - self._anchor).length()), 1.0)

    def _apply_numeric_buffer(self):
        if not self._numeric_buffer:
            return
        try:
            value = float(self._numeric_buffer)
        except ValueError:
            self._numeric_buffer = ""
            return
        self.options[self.primary_value] = value
        self._numeric_buffer = ""

    def _point3(self, point):
        return Vector3(getattr(point, "x", 0.0), getattr(point, "y", 0.0), getattr(point, "z", 0.0))

    def _key_text(self, key):
        return key if isinstance(key, str) else ""


class ExtrudeTool(SolidFeatureTool):
    """Production extrude tool for closed profile solid creation."""

    feature_type = "Extrude"
    primary_value = "distance"
    default_options = {"distance": 100.0, "direction": "Positive", "mid_plane": False, "merge_result": True}

    def _preview_mesh(self, point):
        options = self._feature_options(point)
        return extrude_profile(
            self.parameters.get("profile"),
            options.distance,
            options.mid_plane,
            options.direction,
        )


class RevolveTool(SolidFeatureTool):
    """Production revolve tool for axis-based solid creation."""

    feature_type = "Revolve"
    primary_value = "angle"
    default_options = {"angle": 360.0, "direction": "Positive", "merge_result": True}
    default_parameters = {"axis": "Z", "segments": 36}

    def _primary_numeric(self, point):
        return float(self.options.get("angle", 360.0))

    def _preview_mesh(self, point):
        options = self._feature_options(point)
        return revolve_profile(
            self.parameters.get("profile"),
            options.angle,
            int(self.parameters.get("segments", 36)),
            self.parameters.get("axis", "Z"),
        )


class SweepTool(SolidFeatureTool):
    """Production sweep tool for profile-along-path solid creation."""

    feature_type = "Sweep"
    primary_value = "distance"
    default_options = {"distance": 120.0, "merge_result": True}
    default_parameters = {"segments": 16}

    def _feature_parameters(self, point):
        params = dict(self.parameters)
        if "path" not in params and self._anchor is not None:
            params["path"] = [self._anchor.to_tuple(), point.to_tuple()]
        return params

    def _preview_mesh(self, point):
        params = self._feature_parameters(point)
        return sweep_profile(params.get("profile"), params.get("path"), int(params.get("segments", 16)))


class LoftTool(SolidFeatureTool):
    """Production loft tool for multi-profile solid creation."""

    feature_type = "Loft"
    primary_value = "distance"
    default_options = {"distance": 100.0, "merge_result": True}

    def _feature_parameters(self, point):
        params = dict(self.parameters)
        if "profiles" not in params and self._anchor is not None:
            distance = max(abs((point - self._anchor).length()), 1.0)
            params["profiles"] = [
                [(-50.0, -30.0, -distance * 0.5), (50.0, -30.0, -distance * 0.5), (50.0, 30.0, -distance * 0.5), (-50.0, 30.0, -distance * 0.5)],
                [(-35.0, -20.0, distance * 0.5), (35.0, -20.0, distance * 0.5), (35.0, 20.0, distance * 0.5), (-35.0, 20.0, distance * 0.5)],
            ]
        return params

    def _preview_mesh(self, point):
        return loft_profiles(self._feature_parameters(point).get("profiles"))
