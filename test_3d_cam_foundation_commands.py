from engine.commands import AddCAMObjectCommand
from engine.product import CAMDocument, CAMJob, ManufacturingSetup, OperationDefinition, ProductPart, StockDefinition
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
manager.create_document("Command CAM Product")
part = manager.add_part(ProductPart("Command CAM Part", "mesh-001"))

cam_document = CAMDocument("Command CAM Document")
job = CAMJob("Command CAM Job", cam_document.id, [part.id])
setup = ManufacturingSetup("Command CAM Setup", job.id, StockDefinition("Box", [part.id]))
operation = OperationDefinition("Command Facing", job.id, setup.id, "Facing", [part.id])

workspace.command_manager.execute(AddCAMObjectCommand(workspace, cam_document))
workspace.command_manager.execute(AddCAMObjectCommand(workspace, job))
workspace.command_manager.execute(AddCAMObjectCommand(workspace, setup))
workspace.command_manager.execute(AddCAMObjectCommand(workspace, operation))

assert manager.cam_documents == [cam_document]
assert manager.cam_jobs == [job]
assert manager.cam_setups == [setup]
assert manager.cam_operations == [operation]
assert job.id in cam_document.job_ids
assert setup.id in job.setup_ids
assert operation.id in job.operation_ids

workspace.command_manager.undo()
assert manager.cam_operations == []
assert operation.id not in job.operation_ids
workspace.command_manager.redo()
assert manager.cam_operations == [operation]
assert operation.id in job.operation_ids

workspace.command_manager.undo()
workspace.command_manager.undo()
assert manager.cam_setups == []
assert setup.id not in job.setup_ids
workspace.command_manager.redo()
assert manager.cam_setups == [setup]
assert setup.id in job.setup_ids

print("3d-cam-foundation-commands-ok")
