from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import (
    EvaluationBatch,
    EvaluationGroup,
    GlobalParameter,
    ProductPart,
    SolverHistory,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
mesh = MeshEntity(MeshData.box(2.0, 2.0, 2.0), name="Solver Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
document = manager.create_document("Solver Product")
part = manager.add_part(ProductPart("Solver Part", "Solver Mesh"))
engine = manager.parametric_manager.create_engine("Solver Engine")
parametric_document = manager.parametric_manager.create_document("Solver Parametric Document", engine, references=[part])
parametric_session = manager.parametric_manager.create_session("Solver Parametric Session", engine, parametric_document, references=[part])
parameter = manager.parameter_manager.add_item(GlobalParameter("Solver Width", 10.0, parameter_type="Length", unit="mm", owner_id=document.id))
graph = manager.dependency_manager.create_graph("Solver Dependency Graph")
manager.dependency_manager.add_edge(parameter, part, "ParameterToPart", graph=graph)

solver = manager.parametric_manager.create_solver("Primary Live Solver", engine)
solver_session = manager.parametric_manager.create_solver_session("Primary Solver Session", solver, engine, parametric_session)
request = manager.parametric_manager.queue_evaluation(parameter, "Parameter Changed", solver, solver_session)
batch = manager.parametric_manager.add_item(EvaluationBatch("Solver Batch", [request.id]))
group = manager.parametric_manager.add_item(EvaluationGroup("Solver Group", [request.id], [batch.id]))
result = manager.parametric_manager.add_evaluation_result(request, "Pending", "Metadata queued only", [part])
history = manager.parametric_manager.add_item(SolverHistory(solver.id, solver_session.id, "Queued", "Queued", "", "Evaluation request queued"))
stats = manager.parametric_manager.statistics()

assert solver.id in engine.solver_ids
assert solver_session.id in solver.session_ids
assert solver.queue.evaluation_queue == [request.id]
assert solver_session.queue.evaluation_queue == [request.id]
assert request.state == "Queued"
assert request.flags.queued is True
assert request.context.parameter_ids == [parameter.id]
assert parameter.value == 10.0
assert result.state == "Pending"
assert result.affected_object_ids == [part.id]
assert history.id in solver.history_ids
assert batch.id in solver.evaluation_batch_ids
assert group.id in solver.evaluation_group_ids
assert stats.engines == 1
assert manager.solver_statistics.solvers == 1
assert manager.solver_statistics.evaluation_requests == 1
assert manager.evaluation_statistics.requests == 1
assert manager.evaluation_statistics.queued == 1
assert len(workspace.scene3d.entities()) == 1

print("3d-parametric-live-solver-manager-ok")
