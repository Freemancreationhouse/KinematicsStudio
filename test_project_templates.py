from engine.storage import ProjectSerializer, ProjectTemplate, ProjectTemplateManager


manager = ProjectTemplateManager()

blank = manager.create_workspace(ProjectTemplateManager.BLANK)
assert blank.project_settings["template"] == ProjectTemplateManager.BLANK
assert blank.layer_manager.get("0") is not None

architectural = manager.create_workspace(ProjectTemplateManager.ARCHITECTURAL)
assert architectural.layer_manager.get("Walls") is not None
assert architectural.current_layer.name == "Walls"
assert architectural.current_dimension_style.name == "Architectural"
assert architectural.pattern_manager.get("EARTH") is not None
assert architectural.project_settings["units"] == "Architectural"

mechanical = manager.create_workspace(ProjectTemplateManager.MECHANICAL)
assert mechanical.layer_manager.get("Parts") is not None
assert mechanical.layer_manager.get("Centerlines").line_type == "Center"
assert mechanical.current_dimension_style.name == "Mechanical"
assert mechanical.project_settings["units"] == "Millimeter"

custom = ProjectTemplate(
    "Custom Template",
    layers=[{"name": "Custom Layer", "color": "#123456"}],
    settings={"units": "Custom"},
    current_layer="Custom Layer",
)
manager.register(custom)
custom_workspace = manager.create_workspace("Custom Template")
assert custom_workspace.current_layer.name == "Custom Layer"
assert custom_workspace.project_settings["template"] == "Custom Template"

payload = ProjectSerializer().to_dict(custom_workspace)
loaded = ProjectSerializer().from_dict(payload)
assert loaded.project_settings["template"] == "Custom Template"
assert loaded.project_settings["units"] == "Custom"

print("project-templates-ok")
