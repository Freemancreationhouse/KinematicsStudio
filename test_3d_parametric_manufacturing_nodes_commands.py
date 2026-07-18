from engine.commands import AddManufacturingNodeCommand
from engine.product import ManufacturingNodeCategory, ManufacturingNodeDefinition, ManufacturingNodeLibrary, ManufacturingNodeTemplate
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command Manufacturing Node Engine")
library = ManufacturingNodeLibrary("Command Manufacturing Library", engine.id)
category = ManufacturingNodeCategory("Command CAM Nodes", library.id, "CAM Operation", "Milling")
definition = ManufacturingNodeDefinition("Command Facing Node", library.id, category.id, "CAM Operation", "Facing")
template = ManufacturingNodeTemplate("Command Facing Template", library.id, definition.id)

for item in (library, category, definition, template):
    workspace.command_manager.execute(AddManufacturingNodeCommand(workspace, item))

assert manager.manufacturing_node_libraries == [library]
assert manager.manufacturing_node_categories == [category]
assert manager.manufacturing_node_definitions == [definition]
assert manager.manufacturing_node_templates == [template]

workspace.command_manager.undo()
assert manager.manufacturing_node_templates == []
workspace.command_manager.redo()
assert manager.manufacturing_node_templates == [template]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.manufacturing_node_templates == []
assert manager.manufacturing_node_definitions == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.manufacturing_node_definitions == [definition]
assert manager.manufacturing_node_templates == [template]

print("3d-parametric-manufacturing-nodes-commands-ok")
