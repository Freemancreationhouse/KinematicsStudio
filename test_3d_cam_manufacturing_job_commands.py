from engine.commands import AddManufacturingJobObjectCommand, AddManufacturingValidationCommand
from engine.product import ManufacturingJob, ManufacturingValidationResult, SetupSheet, ValidationProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

job = ManufacturingJob("Command Manufacturing Job")
sheet = SetupSheet("Command Setup Sheet", job.id)
profile = ValidationProfile("Command Validation Profile")
result = ManufacturingValidationResult("Command Validation Result", profile.id, job.id, "Ready")

job_command = AddManufacturingJobObjectCommand(workspace, job)
sheet_command = AddManufacturingJobObjectCommand(workspace, sheet)
profile_command = AddManufacturingValidationCommand(workspace, profile)
result_command = AddManufacturingValidationCommand(workspace, result)

for command in (job_command, sheet_command, profile_command, result_command):
    command.execute()

assert job in manager.manufacturing_jobs
assert sheet in manager.setup_sheets
assert profile in manager.manufacturing_validation_profiles
assert result in manager.manufacturing_validation_results

for command in (result_command, profile_command, sheet_command, job_command):
    command.undo()

assert job not in manager.manufacturing_jobs
assert sheet not in manager.setup_sheets
assert profile not in manager.manufacturing_validation_profiles
assert result not in manager.manufacturing_validation_results

print("3d-cam-manufacturing-job-commands-ok")
