from engine.scene_organization import DisplayPresetManager, ViewFilter
from engine.view_states import VisualStyle
from engine.workspace import Workspace


workspace = Workspace("3D Preset Workspace")
workspace.display_mode_manager.set_mode("x_ray")
workspace.visual_style_manager.add(VisualStyle("Preset Style", background="#010101"))
workspace.visual_style_manager.set_current("Preset Style")
filter_item = workspace.view_filter_manager.add(ViewFilter("Preset Filter", entity_types=["MeshEntity"]))
collection = workspace.scene_collection_manager.create("Preset Collection")
collection.isolated = True

manager = DisplayPresetManager()
preset = manager.save("Presentation", workspace)
assert preset.display_mode == "x_ray"
assert preset.visual_style == "Preset Style"
assert preset.view_filter == "Preset Filter"
assert preset.isolated_collections == ["Preset Collection"]

workspace.display_mode_manager.set_mode("wireframe")
workspace.visual_style_manager.set_current("Default")
filter_item.enabled = False
collection.isolated = False

manager.restore("Presentation", workspace)
assert workspace.display_mode_manager.current_mode == "x_ray"
assert workspace.visual_style_manager.current.name == "Preset Style"
assert workspace.view_filter_manager.active.name == "Preset Filter"
assert collection.isolated is True

restored = DisplayPresetManager()
restored.from_dict(manager.to_dict())
assert restored.names() == ["Presentation"]

print("3d-display-presets-ok")
