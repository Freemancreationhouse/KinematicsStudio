from engine.commands import AddMachineLibraryObjectCommand
from engine.product import MachineLibrary, RouterMachine
from engine.workspace.workspace import Workspace


workspace = Workspace()
manager = workspace.product_manager
library = MachineLibrary("Command Machine Library")
machine = RouterMachine("Command Router", library.id)
profile = manager.machine_library_manager.create_profile(machine, name="Command Profile")
manager.remove_object(profile)

library_command = AddMachineLibraryObjectCommand(workspace, library)
machine_command = AddMachineLibraryObjectCommand(workspace, machine)
profile_command = AddMachineLibraryObjectCommand(workspace, profile)

library_command.execute()
machine_command.execute()
profile_command.execute()

assert library in manager.machine_libraries
assert machine in manager.machine_definitions
assert profile in manager.machine_profiles
assert machine.id in library.machine_ids
assert profile.id in machine.profile_ids

profile_command.undo()
machine_command.undo()
library_command.undo()

assert profile not in manager.machine_profiles
assert machine not in manager.machine_definitions
assert library not in manager.machine_libraries

print("3d-cam-machine-library-commands-ok")
