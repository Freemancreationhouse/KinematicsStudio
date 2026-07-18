from engine.commands import AddDataTreeCommand
from engine.product import DataBranch, DataFlow, DataItem, DataPath, DataTree
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command Data Tree Engine")
tree = DataTree("Command Data Tree", engine.id)
branch = DataBranch("Command Branch", tree.id)
path = DataPath("Command Path", tree.id, branch.id, [0])
item = DataItem("Command Item", tree.id, branch.id, path.id, "item-1", "Any")
flow = DataFlow("Command Flow", tree.id, item.id, branch.id)

for product_item in (tree, branch, path, item, flow):
    workspace.command_manager.execute(AddDataTreeCommand(workspace, product_item))

assert manager.data_trees == [tree]
assert manager.data_branches == [branch]
assert manager.data_paths == [path]
assert manager.data_items == [item]
assert manager.data_flows == [flow]

workspace.command_manager.undo()
assert manager.data_flows == []
workspace.command_manager.redo()
assert manager.data_flows == [flow]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.data_flows == []
assert manager.data_items == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.data_items == [item]
assert manager.data_flows == [flow]

print("3d-parametric-data-tree-commands-ok")
