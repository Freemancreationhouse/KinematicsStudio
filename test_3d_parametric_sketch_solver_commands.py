from engine.commands import AddSketchSolverCommand
from engine.geometry import Vector3
from engine.product import ProductPart, SketchLine, SketchPlane
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Sketch Solver Commands", "mm", 3)
part = manager.add_part(ProductPart("Command Sketch Part", "command-mesh", location=Vector3()))
plane = manager.add_sketch_item(SketchPlane("Command Plane"))
sketch = manager.sketch_manager.create_sketch("Command Sketch", part, plane)
manager.add_sketch_item(SketchLine("Command Line", sketch.id, Vector3(), Vector3(1.0, 0.0, 0.0)))

parametric_engine = manager.parametric_manager.create_engine("Command Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Command Execution Engine", parametric_engine)
live_solver = manager.parametric_manager.create_solver("Command Live Solver", parametric_engine)
sketch_solver = manager.parametric_manager.create_sketch_solver(
    "Undoable Sketch Solver",
    parametric_engine,
    execution_engine,
    live_solver,
)
manager.remove_object(sketch_solver)

command = AddSketchSolverCommand(workspace, sketch_solver)
workspace.command_manager.execute(command)
assert sketch_solver in manager.sketch_solvers
assert manager.active_sketch_solver_id == sketch_solver.id

workspace.command_manager.undo()
assert sketch_solver not in manager.sketch_solvers

workspace.command_manager.redo()
assert sketch_solver in manager.sketch_solvers
assert len(workspace.scene3d.entities()) == 0

print("3d-parametric-sketch-solver-commands-ok")
