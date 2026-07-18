from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    NodeCategory,
    NodeDefinition,
    NodeType,
    ProductPart,
    VisualNodeGraphHistory,
    VisualNodeGraphItem,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Node Graph Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Node Graph Part", "Node Graph Mesh"))
engine = manager.parametric_manager.create_engine("Node Graph Engine")
solver = manager.parametric_manager.create_solver("Node Graph Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Primary Node Graph", engine, solver)
document = manager.parametric_manager.create_visual_node_graph_document("Node Graph Document", graph)
graph_workspace = manager.parametric_manager.create_visual_node_graph_workspace("Node Graph Workspace", graph)
session = manager.parametric_manager.create_visual_node_graph_session("Node Graph Session", graph)
category = manager.parametric_manager.add_item(NodeCategory("Parameters"))
node_type = manager.parametric_manager.add_item(NodeType("Parameter Node", category.id))
definition = manager.parametric_manager.add_item(NodeDefinition("Width Node Definition", node_type.id, category.id))
source_node = manager.parametric_manager.create_node(graph, "Width Node", definition)
target_node = manager.parametric_manager.create_node(graph, "Output Node", definition)
output_port = manager.parametric_manager.add_port(source_node, "Width", "Output", "Length")
input_port = manager.parametric_manager.add_port(target_node, "Value", "Input", "Length")
connection = manager.parametric_manager.connect_nodes(graph, source_node, target_node, output_port, input_port, "Width Connection")
group = manager.parametric_manager.add_item(VisualNodeGraphItem("Sizing Group", graph.id, "Group"))
history = manager.parametric_manager.add_item(VisualNodeGraphHistory(graph.id, "Created", "Node graph metadata created"))
stats = manager.parametric_manager.statistics()

assert graph.id in engine.context_ids
assert document.id in graph.document_ids
assert graph_workspace.id in graph.workspace_ids
assert session.id in graph.session_ids
assert source_node.id in graph.node_ids
assert target_node.id in graph.node_ids
assert connection.id in graph.connection_ids
assert group.id in graph.group_ids
assert history.id in graph.history_ids
assert output_port.id in source_node.output_port_ids
assert input_port.id in target_node.input_port_ids
assert connection.id in output_port.connection_ids
assert connection.id in input_port.connection_ids
assert manager.visual_node_graph_statistics.graphs == 1
assert manager.visual_node_graph_statistics.nodes == 2
assert manager.node_statistics.definitions == 1
assert manager.port_statistics.input_ports == 1
assert manager.port_statistics.output_ports == 1
assert manager.connection_statistics.connections == 1
assert stats.engines == 1
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Node Graph Mesh"

print("3d-parametric-visual-node-graph-manager-ok")
