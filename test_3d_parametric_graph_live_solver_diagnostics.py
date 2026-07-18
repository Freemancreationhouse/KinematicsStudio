from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Expression, GlobalParameter
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.add_3d_entity(MeshEntity(MeshData.box(1.0, 1.0, 1.0), name="Diagnostic Mesh"))

manager = workspace.product_manager
parametric_engine = manager.parametric_manager.create_engine("Diagnostic Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Diagnostic Execution", parametric_engine)
solver = manager.parametric_manager.create_solver("Diagnostic Solver", parametric_engine)
solver_session = manager.parametric_manager.create_solver_session("Diagnostic Solver Session", solver, parametric_engine)
parameter = manager.parameter_manager.add_item(GlobalParameter("diagnostic_value", 2.0))
expression = manager.parameter_manager.add_item(Expression("Diagnostic Expression", "diagnostic_value + 1"))

graph = manager.dependency_manager.create_graph("Diagnostic Cycle Graph")
manager.dependency_manager.add_edge(parameter, expression, "ParameterToExpression", graph=graph)
manager.dependency_manager.add_edge(expression, parameter, "ExpressionToParameter", graph=graph)

diagnostics = manager.parametric_manager.validate_dependency_graph(graph)
assert diagnostics["valid"] is False
assert diagnostics["cycle_detected"] is True

results = manager.parametric_manager.run_live_solver(solver, solver_session, graph, [parameter], execution_engine)

assert results == []
assert solver.flags.blocked is True
assert solver.state.state == "Blocked"
assert solver.diagnostics.status == "Blocked"
assert solver.diagnostics.cycle_detected is True
assert graph.flags.cycle_detection_status == "Cycle Detected"
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-graph-live-solver-diagnostics-ok")
