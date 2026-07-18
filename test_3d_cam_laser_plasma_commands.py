from engine.commands import AddLaserPlasmaObjectCommand, UpdateCAMOperationCommand
from engine.product import LaserJob, MaterialProfile, VectorCutOperation
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
cam_document = manager.cam_manager.create_document("Command Laser CAM")
cam_job = manager.cam_manager.create_job(cam_document, "Command Laser CAM Job")
laser_job = LaserJob("Command Laser Job", cam_job.id)
material = MaterialProfile("Command Acrylic", "Acrylic", 3.0)
operation = VectorCutOperation("Command Vector Cut", cam_job.id)
operation.laser_plasma_metadata.material_profile_id = material.id

workspace.command_manager.execute(AddLaserPlasmaObjectCommand(workspace, laser_job))
workspace.command_manager.execute(AddLaserPlasmaObjectCommand(workspace, material))
workspace.command_manager.execute(AddLaserPlasmaObjectCommand(workspace, operation))
assert manager.laser_jobs == [laser_job]
assert manager.material_profiles == [material]
assert manager.cam_operations == [operation]
assert operation.id in cam_job.operation_ids
assert operation.id in laser_job.operation_ids

workspace.command_manager.execute(
    UpdateCAMOperationCommand(
        workspace,
        operation,
        name="Command Vector Cut Updated",
        enabled=False,
        group="Laser",
        order=3,
    )
)
assert operation.name == "Command Vector Cut Updated"
assert operation.metadata.enabled is False
assert operation.metadata.group == "Laser"
assert operation.metadata.order == 3

workspace.command_manager.undo()
assert operation.name == "Command Vector Cut"
assert operation.metadata.enabled is True

workspace.command_manager.redo()
assert operation.metadata.enabled is False

workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.cam_operations == []
assert manager.material_profiles == []
assert manager.laser_jobs == []

print("3d-cam-laser-plasma-commands-ok")
