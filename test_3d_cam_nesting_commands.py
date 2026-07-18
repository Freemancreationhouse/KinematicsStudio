from engine.commands import AddNestingObjectCommand
from engine.product import NestingJob, NestingProfile, StockLibrary, StockProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager

library = StockLibrary("Command Stock Library")
stock = StockProfile("Command Stock", library.id, 100.0, 50.0, 3.0)
profile = NestingProfile("Command Nest Profile", [stock.id])
job = NestingJob("Command Nest Job", profile_id=profile.id)

commands = [
    AddNestingObjectCommand(workspace, library),
    AddNestingObjectCommand(workspace, stock),
    AddNestingObjectCommand(workspace, profile),
    AddNestingObjectCommand(workspace, job),
]

for command in commands:
    command.execute()

assert library in manager.stock_libraries
assert stock in manager.stock_profiles
assert profile in manager.nesting_profiles
assert job in manager.nesting_jobs
assert stock.id in library.profile_ids

for command in reversed(commands):
    command.undo()

assert library not in manager.stock_libraries
assert stock not in manager.stock_profiles
assert profile not in manager.nesting_profiles
assert job not in manager.nesting_jobs

print("3d-cam-nesting-commands-ok")
