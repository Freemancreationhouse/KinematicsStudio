from engine.commands import AddAINodeCommand, AddScriptNodeCommand
from engine.product import AINodeCategory, AINodeDefinition, AINodeLibrary, AINodeTemplate, ScriptNodeCategory, ScriptNodeDefinition, ScriptNodeLibrary, ScriptNodeTemplate
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command AI Script Node Engine")
ai_library = AINodeLibrary("Command AI Library", engine.id)
ai_category = AINodeCategory("Command AI Nodes", ai_library.id, "AI", "Prompt")
ai_definition = AINodeDefinition("Command Prompt Node", ai_library.id, ai_category.id, "AI", "Prompt")
ai_template = AINodeTemplate("Command Prompt Template", ai_library.id, ai_definition.id)
script_library = ScriptNodeLibrary("Command Script Library", engine.id, ai_node_library_id=ai_library.id)
script_category = ScriptNodeCategory("Command Script Nodes", script_library.id, "Script", "Python")
script_definition = ScriptNodeDefinition("Command Python Node", script_library.id, script_category.id, "Script", "Python")
script_template = ScriptNodeTemplate("Command Python Template", script_library.id, script_definition.id)

for item in (ai_library, ai_category, ai_definition, ai_template):
    workspace.command_manager.execute(AddAINodeCommand(workspace, item))
for item in (script_library, script_category, script_definition, script_template):
    workspace.command_manager.execute(AddScriptNodeCommand(workspace, item))

assert manager.ai_node_libraries == [ai_library]
assert manager.ai_node_categories == [ai_category]
assert manager.ai_node_definitions == [ai_definition]
assert manager.ai_node_templates == [ai_template]
assert manager.script_node_libraries == [script_library]
assert manager.script_node_categories == [script_category]
assert manager.script_node_definitions == [script_definition]
assert manager.script_node_templates == [script_template]

workspace.command_manager.undo()
assert manager.script_node_templates == []
workspace.command_manager.redo()
assert manager.script_node_templates == [script_template]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.script_node_templates == []
assert manager.script_node_definitions == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.script_node_definitions == [script_definition]
assert manager.script_node_templates == [script_template]

print("3d-parametric-ai-script-nodes-commands-ok")
