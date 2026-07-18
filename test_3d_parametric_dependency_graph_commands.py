from engine.commands import AddDependencyGraphCommand
from engine.product import DependencyEdge, DependencyGraph, DependencyNode, DependencyPath, DependencyTopology
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

graph = DependencyGraph("Command Dependency Graph")
node_a = DependencyNode("source", "Parameter", "Source", graph_id=graph.id)
node_b = DependencyNode("target", "Expression", "Target", graph_id=graph.id)
edge = DependencyEdge(node_a.id, node_b.id, "ParameterToExpression", graph_id=graph.id)
path = DependencyPath(graph.id, [node_a.id, node_b.id], [edge.id], "CommandPath")
topology = DependencyTopology(graph.id)

for item in (graph, node_a, node_b, edge, path, topology):
    workspace.command_manager.execute(AddDependencyGraphCommand(workspace, item))

assert manager.dependency_graphs == [graph]
assert manager.dependency_nodes == [node_a, node_b]
assert manager.dependency_edges == [edge]
assert manager.dependency_paths == [path]
assert manager.dependency_topologies
assert edge.id in graph.edge_ids

workspace.command_manager.undo()
assert topology not in manager.dependency_topologies
workspace.command_manager.redo()
assert topology in manager.dependency_topologies

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.dependency_paths == []
assert path not in manager.dependency_paths
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.dependency_paths == [path]
assert topology in manager.dependency_topologies

print("3d-parametric-dependency-graph-commands-ok")
