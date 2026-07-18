import os
import tempfile

from engine.cad.application import CADApplication
from engine.geometry import Vector3
from engine.product import Constraint, GlobalParameter, ProductPart, SketchLine, SketchPlane


app = CADApplication()
workspace = app.workspace
manager = workspace.product_manager
manager.create_document("Persisted Sketch Solver", "mm", 3)
part = manager.add_part(ProductPart("Persisted Sketch Part", "persisted-sketch-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Persisted Plane"))
sketch = manager.sketch_manager.create_sketch("Persisted Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Persisted Line", sketch.id, Vector3(), Vector3(5.0, 0.0, 0.0)))
constraint = manager.add_sketch_constraint_item(Constraint("Horizontal", sketch.id, [line.id]))

parametric_engine = manager.parametric_manager.create_engine("Persisted Sketch Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Persisted Sketch Execution", parametric_engine)
live_solver = manager.parametric_manager.create_solver("Persisted Sketch Live Solver", parametric_engine)
sketch_solver = manager.parametric_manager.create_sketch_solver("Persisted Sketch Solver", parametric_engine, execution_engine, live_solver)
parameter = manager.parameter_manager.add_item(GlobalParameter("persisted_sketch_width", 5.0))
graph = manager.dependency_manager.create_graph("Persisted Sketch Graph")
manager.dependency_manager.add_edge(parameter, sketch, "ParameterToSketch", graph=graph)
session = manager.parametric_manager.solve_sketch(sketch, sketch_solver, changed=[parameter], graph=graph, execution_engine=execution_engine)
workspace.selection.select(sketch_solver)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "sketch_solver.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    restored_solver = restored.sketch_solvers[0]
    restored_session = restored.sketch_solve_sessions[0]
    restored_constraint = restored.sketch_constraints[0]

    assert restored_solver.selected is True
    assert restored_solver.state.state == "Completed"
    assert restored_solver.cache.values[sketch.id]["geometry_count"] == 1
    assert restored_session.context.sketch_id == sketch.id
    assert restored_session.evaluation_order.constraint_ids == [constraint.id]
    assert restored_constraint.metadata.status == "Solved"
    assert restored.sketches[0].metadata.properties["solver_id"] == sketch_solver.id
    assert len(restored_workspace.scene3d.entities()) == 0

print("3d-parametric-sketch-solver-persistence-ok")
