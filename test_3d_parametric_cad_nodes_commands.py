from engine.commands import AddCADNodeCommand
from engine.product import CADNodeCategory, CADNodeDefinition, CADNodeLibrary, CADNodeTemplate
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command CAD Node Engine")
library = CADNodeLibrary("Command CAD Library", engine.id)
category = CADNodeCategory("Command Sketch Nodes", library.id, "Sketch")
definition = CADNodeDefinition("Command Line Node", library.id, category.id, "Sketch", "Line")
template = CADNodeTemplate("Command Line Template", library.id, definition.id)

for item in (library, category, definition, template):
    workspace.command_manager.execute(AddCADNodeCommand(workspace, item))

assert manager.cad_node_libraries == [library]
assert manager.cad_node_categories == [category]
assert manager.cad_node_definitions == [definition]
assert manager.cad_node_templates == [template]

workspace.command_manager.undo()
assert manager.cad_node_templates == []
workspace.command_manager.redo()
assert manager.cad_node_templates == [template]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.cad_node_templates == []
assert manager.cad_node_definitions == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.cad_node_definitions == [definition]
assert manager.cad_node_templates == [template]

print("3d-parametric-cad-nodes-commands-ok")
