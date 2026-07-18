import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import GlobalParameter, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Solver Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Solver Part", "Persisted Solver Mesh"))
engine = manager.parametric_manager.create_engine("Persisted Solver Engine")
parametric_session = manager.parametric_manager.create_session("Persisted Parametric Session", engine, references=[part])
parameter = manager.parameter_manager.add_item(GlobalParameter("Persisted Solver Parameter", 5.0))
solver = manager.parametric_manager.create_solver("Persisted Live Solver", engine)
solver_session = manager.parametric_manager.create_solver_session("Persisted Solver Session", solver, engine, parametric_session)
request = manager.parametric_manager.queue_evaluation(parameter, "Parameter Changed", solver, solver_session)
manager.parametric_manager.add_evaluation_result(request, "Pending", "Persisted metadata only", [part])
workspace.selection.select(solver)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "live_solver.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.live_solvers[0].name == "Persisted Live Solver"
    assert restored.live_solvers[0].selected is True
    assert restored.live_solvers[0].queue.evaluation_queue == [request.id]
    assert restored.solver_sessions[0].evaluation_request_ids == [request.id]
    assert restored.evaluation_requests[0].state == "Queued"
    assert restored.evaluation_requests[0].flags.pending is True
    assert restored.evaluation_results[0].state == "Pending"
    assert restored.solver_statistics.solvers == 1
    assert restored.evaluation_statistics.requests == 1
    assert restored.parameters[0].value == 5.0
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-live-solver-persistence-ok")
