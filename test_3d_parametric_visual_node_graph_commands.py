from engine.commands import AddVisualNodeGraphCommand
from engine.product import NodeConnection, VisualNode, VisualNodeGraph, VisualNodePort
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
engine = manager.parametric_manager.create_engine("Command Node Graph Engine")
graph = VisualNodeGraph("Command Node Graph", engine.id)
node = VisualNode("Command Node", graph.id)
port = VisualNodePort("Command Port", node.id, "Input", "Any")
connection = NodeConnection("Command Connection", graph.id, node.id, node.id, port.id, port.id)

for item in (graph, node, port, connection):
    workspace.command_manager.execute(AddVisualNodeGraphCommand(workspace, item))

assert manager.visual_node_graphs == [graph]
assert manager.visual_nodes == [node]
assert manager.node_ports == [port]
assert manager.node_connections == [connection]

workspace.command_manager.undo()
assert manager.node_connections == []
workspace.command_manager.redo()
assert manager.node_connections == [connection]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.node_connections == []
assert manager.node_ports == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.node_ports == [port]
assert manager.node_connections == [connection]

print("3d-parametric-visual-node-graph-commands-ok")
