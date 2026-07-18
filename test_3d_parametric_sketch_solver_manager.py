from engine.geometry import Vector3
from engine.product import (
    Constraint,
    GlobalParameter,
    ProductPart,
    SketchCircle,
    SketchDimension,
    SketchLine,
    SketchPlane,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Sketch Solver Product", "mm", 3)
part = manager.add_part(ProductPart("Sketch Solver Part", "solver-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Solver Front Plane"))
sketch = manager.sketch_manager.create_sketch("Solver Sketch", part, plane)
line = manager.add_sketch_item(SketchLine("Solver Line", sketch.id, Vector3(), Vector3(10.0, 0.0, 0.0)))
circle = manager.add_sketch_item(SketchCircle("Solver Circle", sketch.id, Vector3(3.0, 3.0, 0.0), 1.5))
horizontal = manager.add_sketch_constraint_item(Constraint("Horizontal", sketch.id, [line.id]))
radius = manager.add_sketch_constraint_item(Constraint("Radius", sketch.id, [circle.id]))
dimension = manager.add_sketch_dimension_item(SketchDimension("Linear", 10.0, "mm", sketch.id, [line.id]))

parametric_engine = manager.parametric_manager.create_engine("Sketch Solver Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Sketch Solver Execution Engine", parametric_engine)
live_solver = manager.parametric_manager.create_solver("Sketch Solver Live Solver", parametric_engine)
sketch_solver = manager.parametric_manager.create_sketch_solver(
    "Batch C Sketch Solver",
    parametric_engine,
    execution_engine,
    live_solver,
)
parameter = manager.parameter_manager.add_item(GlobalParameter("sketch_width", 10.0))
dependency_graph = manager.dependency_manager.create_graph("Sketch Solver Dependency Graph")
manager.dependency_manager.add_edge(parameter, sketch, "ParameterToSketch", graph=dependency_graph)

session = manager.parametric_manager.solve_sketch(
    sketch,
    sketch_solver,
    changed=[parameter],
    graph=dependency_graph,
    execution_engine=execution_engine,
)

assert session is not None
assert session.state.state == "Completed"
assert session.metadata.pipeline_stage == "Sketch Solver"
assert session.context.execution_engine_id == execution_engine.id
assert session.context.live_solver_id == live_solver.id
assert session.evaluation_order.sketch_id == sketch.id
assert session.evaluation_order.constraint_ids == [horizontal.id, radius.id]
assert horizontal.metadata.status == "Solved"
assert radius.metadata.status == "Solved"
assert "degrees_of_freedom" in sketch.metadata.properties
assert sketch.metadata.status in ("Under Constrained", "Fully Constrained")
assert sketch_solver.state.state == "Completed"
assert sketch.id in sketch_solver.cache.solved_sketch_ids
assert manager.sketch_solver_statistics.solvers == 1
assert manager.sketch_solver_statistics.sessions == 1
assert len(workspace.scene3d.entities()) == 0
assert part.mesh_entity_id == "solver-mesh"

print("3d-parametric-sketch-solver-manager-ok")
