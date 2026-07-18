from engine.commands import AddBIMNodeCommand
from engine.product import BIMNodeCategory, BIMNodeDefinition, BIMNodeLibrary, BIMNodeTemplate
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command BIM Node Engine")
library = BIMNodeLibrary("Command BIM Library", engine.id)
category = BIMNodeCategory("Command Wall Nodes", library.id, "Architectural", "Architecture")
definition = BIMNodeDefinition("Command Wall Node", library.id, category.id, "Architectural", "Wall")
template = BIMNodeTemplate("Command Wall Template", library.id, definition.id)

for item in (library, category, definition, template):
    workspace.command_manager.execute(AddBIMNodeCommand(workspace, item))

assert manager.bim_node_libraries == [library]
assert manager.bim_node_categories == [category]
assert manager.bim_node_definitions == [definition]
assert manager.bim_node_templates == [template]

workspace.command_manager.undo()
assert manager.bim_node_templates == []
workspace.command_manager.redo()
assert manager.bim_node_templates == [template]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.bim_node_templates == []
assert manager.bim_node_definitions == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.bim_node_definitions == [definition]
assert manager.bim_node_templates == [template]

print("3d-parametric-bim-nodes-commands-ok")
