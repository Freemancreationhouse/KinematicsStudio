import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Expression, GlobalParameter, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Dependency Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Dependency Part", "Persisted Dependency Mesh"))
parameter = manager.parameter_manager.add_item(GlobalParameter("Persisted Parameter", 9.0))
expression = manager.parameter_manager.add_item(Expression("Persisted Expression", "Persisted Parameter"))
graph = manager.dependency_manager.create_graph("Persisted Dependency Graph")
edge = manager.dependency_manager.add_edge(parameter, expression, "ParameterToExpression", graph=graph)
manager.dependency_manager.add_edge(part, parameter, "PartToParameter", graph=graph)
manager.dependency_manager.add_path(graph.node_ids, graph.edge_ids, "PersistedPath", graph)
manager.dependency_manager.mark_metadata_dirty(parameter, graph, [expression], "persisted dirty metadata")
workspace.selection.select(graph)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "dependency_graph.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager
    restored_graph = restored.dependency_graphs[0]
    restored_topology = restored.dependency_topologies[0]

    assert restored_graph.name == "Persisted Dependency Graph"
    assert restored_graph.selected is True
    assert len(restored.dependency_nodes) == 3
    assert len(restored.dependency_edges) == 2
    assert restored.dependency_edges[0].id == edge.id
    assert restored_topology.cycle_detection_status == "Not Checked"
    assert restored_topology.pending_evaluation_ids
    assert restored.dependency_statistics.graphs == 1
    assert restored.dependency_statistics.edges == 2
    assert restored.parameters[0].value == 9.0
    assert restored.expressions[0].evaluation_state == "Not Evaluated"
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-dependency-graph-persistence-ok")
