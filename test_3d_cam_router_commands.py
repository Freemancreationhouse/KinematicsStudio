from engine.commands import AddRouterObjectCommand, UpdateCAMOperationCommand
from engine.product import ProfileCutOperation, RouterJob, RouterMetadataProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
cam_document = manager.cam_manager.create_document("Command Router CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Command Router CAM Job")
router_job = RouterJob("Command Router Job", cam_job.id)
profile = RouterMetadataProfile("Command Router Profile")
operation = ProfileCutOperation("Command Profile Cut", cam_job.id)
operation.router_metadata.router_job_id = router_job.id
operation.router_profile = profile

workspace.command_manager.execute(AddRouterObjectCommand(workspace, router_job))
workspace.command_manager.execute(AddRouterObjectCommand(workspace, profile))
workspace.command_manager.execute(AddRouterObjectCommand(workspace, operation))
assert manager.router_jobs == [router_job]
assert manager.router_metadata_profiles == [profile]
assert manager.cam_operations == [operation]
assert operation.id in cam_job.operation_ids
assert operation.id in router_job.operation_ids

workspace.command_manager.execute(
    UpdateCAMOperationCommand(
        workspace,
        operation,
        name="Command Profile Cut Updated",
        enabled=False,
        group="Router",
        order=5,
    )
)
assert operation.name == "Command Profile Cut Updated"
assert operation.metadata.enabled is False
assert operation.metadata.group == "Router"
assert operation.metadata.order == 5

workspace.command_manager.undo()
assert operation.name == "Command Profile Cut"
assert operation.metadata.enabled is True

workspace.command_manager.redo()
assert operation.metadata.enabled is False

workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.cam_operations == []
assert manager.router_metadata_profiles == []
assert manager.router_jobs == []

print("3d-cam-router-commands-ok")
