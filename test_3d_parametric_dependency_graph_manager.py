from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    DependencyFlags,
    DependencyMetadata,
    Expression,
    GlobalParameter,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Dependency Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
document = manager.create_document("Dependency Product")
part = manager.add_part(ProductPart("Dependency Part", "Dependency Mesh"))
feature_parameter = manager.parameter_manager.add_item(
    GlobalParameter("Dependency Width", 42.0, parameter_type="Length", unit="mm", owner_id=document.id)
)
expression = manager.parameter_manager.add_item(
    Expression("Dependency Expression", "Dependency Width")
)

graph = manager.dependency_manager.create_graph(
    "Primary Dependency Graph",
    "Parametric",
    DependencyMetadata("Release 1.5 Batch C graph metadata"),
    DependencyFlags(),
)
parameter_node = manager.dependency_manager.add_node(feature_parameter, "Parameter", graph=graph, group="Parameters", identifier="width")
expression_node = manager.dependency_manager.add_node(expression, "Expression", graph=graph, group="Expressions", identifier="width_expression")
part_node = manager.dependency_manager.add_node(part, "ProductPart", graph=graph, group="Product", identifier="part")
parameter_edge = manager.dependency_manager.add_edge(feature_parameter, expression, "ParameterToExpression", graph=graph)
part_edge = manager.dependency_manager.add_edge(part, feature_parameter, "PartToParameter", graph=graph)
path = manager.dependency_manager.add_path(
    [part_node, parameter_node, expression_node],
    [part_edge, parameter_edge],
    "PartParameterExpressionPath",
    graph,
)
manager.dependency_manager.mark_metadata_dirty(feature_parameter, graph, [expression], "parameter metadata changed")
stats = manager.dependency_manager.statistics()
topology = next(item for item in manager.dependency_topologies if item.id == graph.topology_id)

assert graph.node_ids == [parameter_node.id, expression_node.id, part_node.id]
assert graph.edge_ids == [parameter_edge.id, part_edge.id]
assert graph.path_ids == [path.id]
assert topology.parent_map[expression_node.id] == [parameter_node.id]
assert topology.child_map[part_node.id] == [parameter_node.id]
assert topology.cycle_detection_status == "Not Checked"
assert topology.evaluation_order_placeholder == []
assert feature_parameter.value == 42.0
assert expression.evaluation_state == "Not Evaluated"
assert parameter_node.dirty is True
assert graph.flags.pending_evaluation is True
assert stats.graphs == 1
assert stats.nodes == 3
assert stats.edges == 2
assert stats.paths == 1
assert stats.topologies == 1
assert stats.dirty_nodes == 1
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-dependency-graph-manager-ok")
