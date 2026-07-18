import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import DataBranch, DataTree, Expression, GlobalParameter, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Reactive Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Reactive Part", "Persisted Reactive Mesh"))
parametric_engine = manager.parametric_manager.create_engine("Persisted Reactive Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Persisted Reactive Execution Engine", parametric_engine)
solver = manager.parametric_manager.create_solver("Persisted Reactive Solver", parametric_engine)
solver_session = manager.parametric_manager.create_solver_session("Persisted Reactive Solver Session", solver, parametric_engine)
width = manager.parameter_manager.add_item(GlobalParameter("persisted_width", 8.0))
expression = manager.parameter_manager.add_item(Expression("Persisted Reactive Expression", "persisted_width * 3"))
dependency_graph = manager.dependency_manager.create_graph("Persisted Reactive Graph")
manager.dependency_manager.add_edge(width, expression, "ParameterToExpression", graph=dependency_graph)
tree = manager.parametric_manager.add_item(DataTree("Persisted Reactive Tree", parametric_engine.id, solver.id, dependency_graph.id))
branch = manager.parametric_manager.add_item(DataBranch("Persisted Reactive Branch", tree.id))

manager.parametric_manager.run_live_solver(solver, solver_session, dependency_graph, [width], execution_engine)
workspace.selection.select(solver)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "reactive_solver.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    restored_solver = restored.live_solvers[0]
    restored_execution = restored.execution_engines[0]
    restored_tree = restored.data_trees[0]
    restored_branch = restored.data_branches[0]

    assert restored_solver.selected is True
    assert restored_solver.state.state == "Completed"
    assert restored_solver.diagnostics.status == "Completed"
    assert restored_solver.execution_context.dependency_graph_id == dependency_graph.id
    assert restored_execution.expression_cache.values[expression.id] == 24.0
    assert restored_tree.metadata.properties["execution_context"]["dependency_graph_id"] == dependency_graph.id
    assert restored_branch.state.state == "Evaluated"
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-graph-live-solver-persistence-ok")
