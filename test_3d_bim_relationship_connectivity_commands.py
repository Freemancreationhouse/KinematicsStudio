from engine.bim import BIMInstance, BIMRelationship, Connection, HostObject, HostedObject, Opening
from engine.commands import (
    AddBIMConnectionCommand,
    AddBIMHostOpeningCommand,
    AddBIMObjectCommand,
    AddBIMRelationshipCommand,
    CreateBIMProjectCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Batch G BIM"))
wall = BIMInstance("Command Wall")
door = BIMInstance("Command Door")
beam = BIMInstance("Command Beam")
workspace.command_manager.execute(AddBIMObjectCommand(workspace, wall))
workspace.command_manager.execute(AddBIMObjectCommand(workspace, door))
workspace.command_manager.execute(AddBIMObjectCommand(workspace, beam))

relationship = BIMRelationship(wall.id, door.id, "Host")
host = HostObject(wall.id, [door.id])
hosted = HostedObject(door.id, wall.id)
opening = Opening("Command Opening", wall.id, "", door.id)
connection = Connection(wall.id, beam.id, "Beam")

workspace.command_manager.execute(AddBIMRelationshipCommand(workspace, relationship))
workspace.command_manager.execute(AddBIMHostOpeningCommand(workspace, host))
workspace.command_manager.execute(AddBIMHostOpeningCommand(workspace, hosted))
workspace.command_manager.execute(AddBIMHostOpeningCommand(workspace, opening))
workspace.command_manager.execute(AddBIMConnectionCommand(workspace, connection))

assert workspace.bim_manager.relationships_for(wall) == [relationship]
assert workspace.bim_manager.hosted_objects_for(wall) == [door]
assert workspace.bim_manager.openings_for(wall) == [opening]
assert workspace.bim_manager.connections_for(wall) == [connection]

workspace.command_manager.undo()
assert workspace.bim_manager.connections_for(wall) == []
workspace.command_manager.redo()
assert workspace.bim_manager.connections_for(wall) == [connection]

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.bim_manager.openings_for(wall) == []
workspace.command_manager.redo()
assert workspace.bim_manager.openings_for(wall) == [opening]

print("3d-bim-relationship-connectivity-commands-ok")
