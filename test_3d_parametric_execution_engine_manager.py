from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Expression, GlobalParameter, NodeCategory, NodeDefinition, NodeMetadata, NodeType, ProductPart
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Execution Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Execution Part", "Execution Mesh"))
parametric_engine = manager.parametric_manager.create_engine("Core Execution Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Core Execution Engine", parametric_engine)
execution_session = manager.parametric_manager.create_execution_session("Core Execution Session", execution_engine, parametric_engine)

width = manager.parameter_manager.add_item(GlobalParameter("width", 10.0, parameter_type="Length", unit="mm"))
height = manager.parameter_manager.add_item(GlobalParameter("height", 5.0, parameter_type="Length", unit="mm"))
expression = manager.parameter_manager.add_item(Expression("Area Expression", "width * height + sqrt(16)", "mm2"))

request = manager.parametric_manager.queue_execution(expression, "Expression Evaluation", execution_engine, execution_session)
result = manager.parametric_manager.execute_request(request)

assert result.status == "Completed"
assert result.value == 54.0
assert result.metadata.pipeline_stage == "Expression"
assert expression.validation_state == "Valid"
assert expression.evaluation_state == "Evaluated"
assert execution_engine.id in parametric_engine.execution_engine_ids
assert execution_session.id in execution_engine.session_ids
assert request.id in execution_engine.queue.request_ids
assert result.id in execution_engine.result_ids
assert execution_engine.cache.values[expression.id] == 54.0
assert execution_engine.expression_cache.values[expression.id] == 54.0

node_category = manager.parametric_manager.add_item(NodeCategory("Execution Nodes"))
node_type = manager.parametric_manager.add_item(NodeType("Math Node Type", node_category.id))
node_definition = manager.parametric_manager.add_item(
    NodeDefinition("Math Node", node_type.id, node_category.id, NodeMetadata(properties={"operation": "Math"}))
)
node_graph = manager.parametric_manager.create_visual_node_graph("Execution Node Graph", parametric_engine)
math_node = manager.parametric_manager.create_node(
    node_graph,
    "Math Execution Node",
    node_definition,
    NodeMetadata(properties={"expression": "width + height"}),
)
node_request = manager.parametric_manager.queue_execution(math_node, "Node Execution", execution_engine, execution_session)
node_result = manager.parametric_manager.execute_request(node_request)

assert node_result.status == "Completed"
assert node_result.value == 15.0
assert node_result.metadata.pipeline_stage == "Node Execution"

dependency_graph = manager.dependency_manager.create_graph("Execution Dependency Graph")
manager.dependency_manager.add_edge(width, expression, "ParameterToExpression", graph=dependency_graph)
manager.dependency_manager.add_edge(expression, part, "ExpressionToPart", graph=dependency_graph)

order = manager.parametric_manager.dependency_order(dependency_graph)
owner_order = [
    next(node.owner_id for node in manager.dependency_nodes if node.id == node_id)
    for node_id in order
]
assert owner_order == [width.id, expression.id, part.id]
assert dependency_graph.flags.cycle_detection_status == "Acyclic"
assert dependency_graph.flags.evaluation_order_status == "Computed"

dirty = manager.parametric_manager.propagate_dirty(width, dependency_graph)
assert expression.id in dirty
assert part.id in dirty
assert dependency_graph.flags.dirty is True

manager.parametric_manager.statistics()
statistics = manager.execution_statistics
assert statistics.engines == 1
assert statistics.requests == 2
assert statistics.completed == 2
assert statistics.expressions == 1
assert statistics.nodes == 1
assert statistics.cache_entries >= 2
assert execution_engine.statistics.completed == 2

assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Execution Mesh"

print("3d-parametric-execution-engine-manager-ok")
