from engine.commands import AddSimulationObjectCommand
from engine.product import SimulationJob, SimulationProfile
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
profile = SimulationProfile("Command Simulation Profile")
job = SimulationJob("Command Simulation Job", profile_id=profile.id)

profile_command = AddSimulationObjectCommand(workspace, profile)
job_command = AddSimulationObjectCommand(workspace, job)

profile_command.execute()
job_command.execute()

assert profile in manager.simulation_profiles
assert job in manager.simulation_jobs

job_command.undo()
profile_command.undo()

assert job not in manager.simulation_jobs
assert profile not in manager.simulation_profiles

print("3d-cam-simulation-commands-ok")
