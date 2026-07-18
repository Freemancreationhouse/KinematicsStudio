from dataclasses import dataclass, field

from engine.workspace import Workspace


@dataclass
class ProjectTemplate:
    """Describes workspace defaults for a new project template."""

    name: str
    layers: list = field(default_factory=list)
    dimension_styles: list = field(default_factory=list)
    patterns: list = field(default_factory=list)
    settings: dict = field(default_factory=dict)
    current_layer: str = "0"
    current_dimension_style: str = "Standard"
    current_pattern: str = "SOLID"


class ProjectTemplateManager:
    """Creates new workspaces from registered project templates."""

    BLANK = "Blank Project"
    ARCHITECTURAL = "Architectural Template"
    MECHANICAL = "Mechanical Template"

    def __init__(self):

        self._templates = {}
        self._register_defaults()

    # --------------------------------

    def register(self, template):
        """Register a custom or built-in project template."""

        self._templates[template.name] = template

        return template

    # --------------------------------

    def get(self, name):
        """Return a template by name."""

        return self._templates.get(name)

    # --------------------------------

    def names(self):
        """Return template names in registration order."""

        return list(self._templates.keys())

    # --------------------------------

    def create_workspace(self, template_name=BLANK, workspace_name="Model"):
        """Create a workspace initialized from a project template."""

        template = self.get(template_name) or self.get(self.BLANK)
        workspace = Workspace(workspace_name)
        workspace.project_settings.update(template.settings)
        workspace.project_settings["template"] = template.name

        self._apply_layers(workspace, template)
        self._apply_dimension_styles(workspace, template)
        self._apply_patterns(workspace, template)

        return workspace

    # --------------------------------

    def _apply_layers(self, workspace, template):

        for values in template.layers:
            layer = workspace.create_layer(
                values["name"],
                values.get("color", "#FFFFFF"),
                values.get("line_type", "Continuous"),
                values.get("line_weight", 1.0),
            )
            layer.visible = values.get("visible", True)
            layer.locked = values.get("locked", False)

        workspace.set_current_layer(template.current_layer)

    # --------------------------------

    def _apply_dimension_styles(self, workspace, template):

        for values in template.dimension_styles:
            workspace.create_dimension_style(values["name"], **{
                key: value
                for key, value in values.items()
                if key != "name"
            })

        workspace.set_current_dimension_style(template.current_dimension_style)

    # --------------------------------

    def _apply_patterns(self, workspace, template):

        for values in template.patterns:
            workspace.pattern_manager.create(
                values["name"],
                values.get("pattern_type", "lines"),
                values.get("scale", 10.0),
                values.get("angle", 45.0),
            )

        workspace.set_current_pattern(template.current_pattern)

    # --------------------------------

    def _register_defaults(self):

        self.register(ProjectTemplate(
            self.BLANK,
            settings={
                "units": "Decimal",
                "autosave_enabled": True,
            },
        ))
        self.register(ProjectTemplate(
            self.ARCHITECTURAL,
            layers=[
                {"name": "Walls", "color": "#FFFFFF", "line_weight": 0.50},
                {"name": "Doors", "color": "#00CCFF", "line_weight": 0.35},
                {"name": "Windows", "color": "#66FF66", "line_weight": 0.35},
                {"name": "Annotations", "color": "#FFFF66", "line_weight": 0.18},
                {"name": "Hatch", "color": "#999999", "line_weight": 0.18},
            ],
            dimension_styles=[
                {
                    "name": "Architectural",
                    "text_height": 9.0,
                    "arrow_size": 4.0,
                    "precision": 2,
                    "units": "Architectural",
                }
            ],
            patterns=[
                {"name": "EARTH", "pattern_type": "lines", "scale": 24.0, "angle": 30.0},
            ],
            settings={
                "units": "Architectural",
                "drawing_scale": "1:100",
                "autosave_enabled": True,
            },
            current_layer="Walls",
            current_dimension_style="Architectural",
            current_pattern="ANSI31",
        ))
        self.register(ProjectTemplate(
            self.MECHANICAL,
            layers=[
                {"name": "Parts", "color": "#FFFFFF", "line_weight": 0.35},
                {"name": "Centerlines", "color": "#FF66FF", "line_type": "Center", "line_weight": 0.18},
                {"name": "Dimensions", "color": "#FFFF66", "line_weight": 0.18},
                {"name": "Hidden", "color": "#6666FF", "line_type": "Hidden", "line_weight": 0.18},
                {"name": "Hatch", "color": "#999999", "line_weight": 0.18},
            ],
            dimension_styles=[
                {
                    "name": "Mechanical",
                    "text_height": 3.5,
                    "arrow_size": 2.5,
                    "precision": 3,
                    "units": "Millimeter",
                }
            ],
            patterns=[
                {"name": "STEEL", "pattern_type": "lines", "scale": 3.0, "angle": 45.0},
            ],
            settings={
                "units": "Millimeter",
                "drawing_scale": "1:1",
                "autosave_enabled": True,
            },
            current_layer="Parts",
            current_dimension_style="Mechanical",
            current_pattern="ANSI31",
        ))
