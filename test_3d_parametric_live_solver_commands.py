from engine.commands import AddLiveSolverCommand
from engine.product import EvaluationRequest, LiveSolver, SolverSession
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

engine = manager.parametric_manager.create_engine("Command Solver Engine")
solver = LiveSolver("Command Live Solver", engine.id)
solver_session = SolverSession("Command Solver Session", solver.id, engine.id)
request = EvaluationRequest("Command Request", "Workspace Changed", "workspace")

for item in (solver, solver_session, request):
    workspace.command_manager.execute(AddLiveSolverCommand(workspace, item))

assert manager.live_solvers == [solver]
assert manager.solver_sessions == [solver_session]
assert manager.evaluation_requests == [request]

workspace.command_manager.undo()
assert manager.evaluation_requests == []
workspace.command_manager.redo()
assert manager.evaluation_requests == [request]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.evaluation_requests == []
assert manager.solver_sessions == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.solver_sessions == [solver_session]
assert manager.evaluation_requests == [request]

print("3d-parametric-live-solver-commands-ok")
