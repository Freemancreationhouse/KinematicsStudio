from engine.commands import AddCAMObjectCommand, UpdateCAMOperationCommand
from engine.product import FacingOperation, OperationParameters
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
cam_document = manager.cam_manager.create_document("Command 25 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "Command 25 Axis Job")
setup = manager.manufacturing_setup_manager.create_setup(job, name="Command Setup")
operation = FacingOperation(
    "Command Facing",
    job.id,
    setup.id,
    target_ids=[],
    parameters=OperationParameters(depth=2.0, step_down=0.5),
)

workspace.command_manager.execute(AddCAMObjectCommand(workspace, operation))
assert manager.cam_operations == [operation]
assert operation.id in job.operation_ids

workspace.command_manager.execute(
    UpdateCAMOperationCommand(
        workspace,
        operation,
        name="Command Facing Updated",
        enabled=False,
        group="Roughing",
        order=5,
    )
)
assert operation.name == "Command Facing Updated"
assert operation.metadata.enabled is False
assert operation.metadata.group == "Roughing"
assert operation.metadata.order == 5

workspace.command_manager.undo()
assert operation.name == "Command Facing"
assert operation.metadata.enabled is True
assert operation.metadata.group == ""
assert operation.metadata.order == 0

workspace.command_manager.redo()
assert operation.name == "Command Facing Updated"
assert operation.metadata.enabled is False

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.cam_operations == []
assert operation.id not in job.operation_ids

print("3d-cam-25-axis-commands-ok")
