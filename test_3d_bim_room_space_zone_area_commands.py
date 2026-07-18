from engine.bim import AreaRegion, BIMInstance, Room, Space, Zone
from engine.commands import (
    AddBIMAreaAnalysisCommand,
    AddBIMObjectCommand,
    AddBIMRoomCommand,
    AddBIMSpaceCommand,
    AddBIMZoneCommand,
    CreateBIMProjectCommand,
)
from engine.workspace.workspace import Workspace


workspace = Workspace()
workspace.command_manager.execute(CreateBIMProjectCommand(workspace, "Command Batch I BIM"))
room_element = BIMInstance("Command Room Element")
space_element = BIMInstance("Command Space Element")
workspace.command_manager.execute(AddBIMObjectCommand(workspace, room_element))
workspace.command_manager.execute(AddBIMObjectCommand(workspace, space_element))

room = Room("201", "Command Room", element_id=room_element.id, area=80.0)
space = Space("Command Space", room.id, space_element.id, 70.0)
zone = Zone("Command Zone", [room.id], [space.id])
region = AreaRegion("Command Gross", "Gross Area", [room.id], [space.id])

workspace.command_manager.execute(AddBIMRoomCommand(workspace, room))
workspace.command_manager.execute(AddBIMSpaceCommand(workspace, space))
workspace.command_manager.execute(AddBIMZoneCommand(workspace, zone))
workspace.command_manager.execute(AddBIMAreaAnalysisCommand(workspace, region))

assert workspace.bim_manager.rooms_for(room_element) == [room]
assert workspace.bim_manager.spaces_for(space_element) == [space]
assert workspace.bim_manager.zones_for(room) == [zone]
assert workspace.bim_manager.active_project.area_summary.gross_area == 150.0

workspace.command_manager.undo()
assert workspace.bim_manager.active_project.area_regions == []
workspace.command_manager.redo()
assert workspace.bim_manager.active_project.area_summary.gross_area == 150.0

workspace.command_manager.undo()
workspace.command_manager.undo()
assert workspace.bim_manager.active_project.zones == []
workspace.command_manager.redo()
assert workspace.bim_manager.active_project.zones == [zone]

print("3d-bim-room-space-zone-area-commands-ok")
