import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import ProductPart, VisualNodeGraphItem


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Node Graph Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Node Graph Part", "Persisted Node Graph Mesh"))
engine = manager.parametric_manager.create_engine("Persisted Node Graph Engine")
solver = manager.parametric_manager.create_solver("Persisted Node Graph Solver", engine)
graph = manager.parametric_manager.create_visual_node_graph("Persisted Visual Graph", engine, solver)
node = manager.parametric_manager.create_node(graph, "Persisted Node")
out_port = manager.parametric_manager.add_port(node, "Out", "Output", "Any")
in_port = manager.parametric_manager.add_port(node, "In", "Input", "Any")
connection = manager.parametric_manager.connect_nodes(graph, node, node, out_port, in_port, "Persisted Connection")
manager.parametric_manager.add_item(VisualNodeGraphItem("Persisted Comment", graph.id, "Comment"))
workspace.selection.select(graph)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "visual_node_graph.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.visual_node_graphs[0].name == "Persisted Visual Graph"
    assert restored.visual_node_graphs[0].selected is True
    assert restored.visual_node_graphs[0].node_ids == [node.id]
    assert restored.visual_node_graphs[0].connection_ids == [connection.id]
    assert restored.visual_nodes[0].name == "Persisted Node"
    assert len(restored.node_ports) == 2
    assert restored.node_connections[0].name == "Persisted Connection"
    assert restored.visual_node_graph_items[0].item_type == "Comment"
    assert restored.visual_node_graph_statistics.graphs == 1
    assert restored.port_statistics.input_ports == 1
    assert restored.port_statistics.output_ports == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-visual-node-graph-persistence-ok")
