from engine.commands import AddSlicerObjectCommand
from engine.product import SliceJob, SliceOperation, SliceProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
profile = SliceProfile("Command Slice Profile")
job = SliceJob("Command Slice Job", profile_id=profile.id)
operation = SliceOperation("Command Slice Operation", job.id, profile_id=profile.id)

profile_command = AddSlicerObjectCommand(workspace, profile)
job_command = AddSlicerObjectCommand(workspace, job)
operation_command = AddSlicerObjectCommand(workspace, operation)

profile_command.execute()
job_command.execute()
operation_command.execute()

assert profile in manager.slice_profiles
assert job in manager.slice_jobs
assert operation in manager.slice_operations
assert operation.id in job.operation_ids

operation_command.undo()
job_command.undo()
profile_command.undo()

assert operation not in manager.slice_operations
assert job not in manager.slice_jobs
assert profile not in manager.slice_profiles

print("3d-cam-slicer-commands-ok")
