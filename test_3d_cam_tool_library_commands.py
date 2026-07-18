from engine.commands import AddToolLibraryCommand
from engine.product import EndMill, FeedSpeedProfile, ToolCategory, ToolHolder, ToolLibrary, ToolPreset
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

library = ToolLibrary("Command Tool Library")
category = ToolCategory("Command Mills", library.id)
tool = EndMill("Command End Mill", library.id, category.id, 6.0, 20.0, 60.0, 4)
holder = ToolHolder("Command Holder", "Holder", library.id, 80.0, 55.0)
profile = FeedSpeedProfile("Command Feeds", tool.id)
preset = ToolPreset("Command Preset", tool.id, holder.id, profile.id, 7, 7, 7)

for item in (library, category, tool, holder, profile, preset):
    workspace.command_manager.execute(AddToolLibraryCommand(workspace, item))

assert manager.tool_libraries == [library]
assert manager.tool_categories == [category]
assert manager.tool_definitions == [tool]
assert manager.tool_holders == [holder]
assert manager.feed_speed_profiles == [profile]
assert manager.tool_presets == [preset]
assert tool.id in library.tool_ids
assert holder.id in library.holder_ids
assert preset.id in tool.preset_ids

workspace.command_manager.undo()
assert manager.tool_presets == []
assert preset.id not in tool.preset_ids
workspace.command_manager.redo()
assert manager.tool_presets == [preset]
assert preset.id in tool.preset_ids

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.feed_speed_profiles == []
workspace.command_manager.redo()
assert manager.feed_speed_profiles == [profile]

print("3d-cam-tool-library-commands-ok")
