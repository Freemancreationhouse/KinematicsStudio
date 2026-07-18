from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    DataBranch,
    DataTree,
    Expression,
    GlobalParameter,
    NodeCategory,
    NodeDefinition,
    NodeMetadata,
    NodeType,
    ProductPart,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Live Solver Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Live Solver Part", "Live Solver Mesh"))
parametric_engine = manager.parametric_manager.create_engine("Live Solver Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Live Solver Execution Engine", parametric_engine)
solver = manager.parametric_manager.create_solver("Batch B Live Solver", parametric_engine)
solver_session = manager.parametric_manager.create_solver_session("Batch B Solver Session", solver, parametric_engine)

width = manager.parameter_manager.add_item(GlobalParameter("width", 12.0, parameter_type="Length", unit="mm"))
height = manager.parameter_manager.add_item(GlobalParameter("height", 2.0, parameter_type="Length", unit="mm"))
expression = manager.parameter_manager.add_item(Expression("Reactive Expression", "width * height", "mm2"))

node_category = manager.parametric_manager.add_item(NodeCategory("Reactive Nodes"))
node_type = manager.parametric_manager.add_item(NodeType("Math", node_category.id))
node_definition = manager.parametric_manager.add_item(
    NodeDefinition("Math Node", node_type.id, node_category.id, NodeMetadata(properties={"operation": "Math"}))
)
visual_graph = manager.parametric_manager.create_visual_node_graph("Reactive Visual Graph", parametric_engine, solver)
math_node = manager.parametric_manager.create_node(
    visual_graph,
    "Reactive Math Node",
    node_definition,
    NodeMetadata(properties={"expression": "width + height"}),
)

dependency_graph = manager.dependency_manager.create_graph("Reactive Dependency Graph")
manager.dependency_manager.add_edge(width, expression, "ParameterToExpression", graph=dependency_graph)
manager.dependency_manager.add_edge(height, expression, "ParameterToExpression", graph=dependency_graph)
manager.dependency_manager.add_edge(expression, math_node, "ExpressionToNode", graph=dependency_graph)

tree = manager.parametric_manager.add_item(DataTree("Reactive Data Tree", parametric_engine.id, solver.id, dependency_graph.id))
branch = manager.parametric_manager.add_item(DataBranch("Reactive Branch", tree.id))

diagnostics = manager.parametric_manager.validate_dependency_graph(dependency_graph)
assert diagnostics["valid"] is True
assert diagnostics["cycle_detected"] is False

results = manager.parametric_manager.run_live_solver(solver, solver_session, dependency_graph, [width], execution_engine)

assert results
assert solver.state.state == "Completed"
assert solver.diagnostics.status == "Completed"
assert solver.execution_context.dependency_graph_id == dependency_graph.id
assert expression.id in solver.execution_context.executed_object_ids
assert math_node.id in solver.execution_context.executed_object_ids
assert expression.evaluation_state == "Evaluated"
assert execution_engine.expression_cache.values[expression.id] == 24.0
assert math_node.flags.execution_status == "Completed"
assert math_node.state.properties["last_value"] == 14.0
assert visual_graph.flags.execution_status == "Completed"
assert visual_graph.metadata.properties["execution_order"]
assert branch.state.state == "Evaluated"
assert branch.state.properties["execution_graph_id"] == dependency_graph.id
assert tree.metadata.properties["execution_context"]["dependency_graph_id"] == dependency_graph.id
assert len(workspace.scene3d.entities()) == 1
assert part.mesh_entity_id == "Live Solver Mesh"

second_results = manager.parametric_manager.run_live_solver(solver, solver_session, dependency_graph, [], execution_engine)
assert len(second_results) < len(results)
assert solver.execution_context.skipped_object_ids

print("3d-parametric-graph-live-solver-manager-ok")
