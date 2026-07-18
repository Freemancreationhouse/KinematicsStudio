from engine.commands import AddExecutionObjectCommand
from engine.product import ExecutionBatch, ExecutionRequest
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
parametric_engine = manager.parametric_manager.create_engine("Command Execution Parametric Engine")
execution_engine = manager.parametric_manager.create_execution_engine("Command Execution Engine", parametric_engine)
execution_session = manager.parametric_manager.create_execution_session("Command Execution Session", execution_engine, parametric_engine)
execution_request = ExecutionRequest("Command Execution Request", "target-1")
execution_batch = ExecutionBatch("Command Execution Batch", [execution_request.id])

manager.remove_object(execution_engine)
manager.remove_object(execution_session)

for item in (execution_engine, execution_session, execution_request, execution_batch):
    workspace.command_manager.execute(AddExecutionObjectCommand(workspace, item))

assert manager.execution_engines == [execution_engine]
assert manager.execution_sessions == [execution_session]
assert manager.execution_requests == [execution_request]
assert manager.execution_batches == [execution_batch]
assert manager.active_execution_engine_id == execution_engine.id

workspace.command_manager.undo()
assert manager.execution_batches == []
workspace.command_manager.redo()
assert manager.execution_batches == [execution_batch]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.execution_batches == []
assert manager.execution_requests == []
workspace.command_manager.redo()
workspace.command_manager.redo()
assert manager.execution_requests == [execution_request]
assert manager.execution_batches == [execution_batch]

print("3d-parametric-execution-engine-commands-ok")
