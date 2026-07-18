import os
import tempfile

from engine.cad.application import CADApplication
from engine.entities import MeshEntity
from engine.geometry import MeshData
from engine.product import Expression, GlobalParameter, ProductPart


app = CADApplication()
workspace = app.workspace
mesh = MeshEntity(MeshData.box(1.0, 2.0, 3.0), name="Persisted Execution Mesh")
workspace.add_3d_entity(mesh)

manager = workspace.product_manager
part = manager.add_part(ProductPart("Persisted Execution Part", "Persisted Execution Mesh"))
parametric_engine = manager.parametric_manager.create_engine("Persisted Execution Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Persisted Execution Engine", parametric_engine)
execution_session = manager.parametric_manager.create_execution_session("Persisted Execution Session", execution_engine, parametric_engine)

manager.parameter_manager.add_item(GlobalParameter("persisted_width", 7.0, parameter_type="Length", unit="mm"))
manager.parameter_manager.add_item(GlobalParameter("persisted_height", 3.0, parameter_type="Length", unit="mm"))
expression = manager.parameter_manager.add_item(Expression("Persisted Expression", "persisted_width * persisted_height", "mm2"))
request = manager.parametric_manager.queue_execution(expression, "Expression Evaluation", execution_engine, execution_session)
result = manager.parametric_manager.execute_request(request)
workspace.selection.select(execution_engine)

with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "execution_engine.ksproj")
    app.save_project(path)

    opened = CADApplication()
    restored_workspace = opened.open_project(path)
    restored = restored_workspace.product_manager

    assert restored.execution_engines[0].name == execution_engine.name
    assert restored.execution_engines[0].selected is True
    assert restored.execution_sessions[0].name == execution_session.name
    assert restored.execution_requests[0].metadata.status == "Completed"
    assert restored.execution_results[0].status == "Completed"
    assert restored.execution_results[0].value == result.value
    assert restored.execution_results[0].metadata.pipeline_stage == "Expression"
    assert restored.execution_engines[0].cache.values[expression.id] == 21.0
    assert restored.execution_engines[0].expression_cache.values[expression.id] == 21.0
    assert restored.execution_statistics.engines == 1
    assert restored.execution_statistics.completed == 1
    assert restored.parts[0].mesh_entity_id == part.mesh_entity_id
    assert len(restored_workspace.scene3d.entities()) == 1

print("3d-parametric-execution-engine-persistence-ok")
