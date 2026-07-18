from engine.commands import AddThreeAxisCAMObjectCommand, UpdateCAMOperationCommand
from engine.product import ParallelOperation, SurfaceSelection, ThreeAxisStrategy
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
cam_document = manager.cam_manager.create_document("Command 3 Axis CAM")
job = manager.cam_manager.create_job(cam_document, "Command 3 Axis Job")
setup = manager.manufacturing_setup_manager.create_setup(job, name="Command 3 Axis Setup")

surface_selection = SurfaceSelection("Command Surface Selection")
operation = ParallelOperation("Command Parallel", job.id, setup.id)
operation.strategy = ThreeAxisStrategy("Parallel", tolerance=0.03, stepover=0.25)
operation.three_axis_metadata.surface_selection_id = surface_selection.id

workspace.command_manager.execute(AddThreeAxisCAMObjectCommand(workspace, surface_selection))
workspace.command_manager.execute(AddThreeAxisCAMObjectCommand(workspace, operation))
assert manager.three_axis_surface_selections == [surface_selection]
assert manager.cam_operations == [operation]
assert operation.id in job.operation_ids

workspace.command_manager.execute(
    UpdateCAMOperationCommand(
        workspace,
        operation,
        name="Command Parallel Updated",
        enabled=False,
        group="Finishing",
        order=4,
    )
)
assert operation.name == "Command Parallel Updated"
assert operation.metadata.enabled is False
assert operation.metadata.group == "Finishing"
assert operation.metadata.order == 4

workspace.command_manager.undo()
assert operation.name == "Command Parallel"
assert operation.metadata.enabled is True
assert operation.metadata.group == ""

workspace.command_manager.redo()
assert operation.metadata.enabled is False

workspace.command_manager.undo()
workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.cam_operations == []
assert manager.three_axis_surface_selections == []
assert operation.id not in job.operation_ids

print("3d-cam-3-axis-commands-ok")
